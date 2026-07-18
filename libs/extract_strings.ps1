<#
.SYNOPSIS
    Extracts C# string literals (field constants + ldstr operands) from a .NET assembly
    using dnlib. Invoked by Python (candidates.py) via PowerShell.

.PARAMETER DllPath
    Path to the target assembly (e.g. Assembly-CSharp.dll).

.PARAMETER OutFile
    Path where the extracted strings (one per line, UTF-8) will be written.
#>
param(
    [Parameter(Mandatory = $true)][string]$DllPath,
    [Parameter(Mandatory = $true)][string]$OutFile
)

$ErrorActionPreference = 'Stop'

# Locate dnlib.dll next to this script.
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$dnlibPath = Join-Path $scriptDir 'dnlib.dll'
if (-not (Test-Path $dnlibPath)) {
    # Fallback: look in the project libs folder one level up.
    $dnlibPath = Join-Path (Split-Path -Parent $scriptDir) 'dnlib.dll'
}
if (-not (Test-Path $dnlibPath)) {
    Write-Error "dnlib.dll not found near script."
    exit 1
}

# Load dnlib into the current AppDomain.
[void][System.Reflection.Assembly]::LoadFrom($dnlibPath)

$mod = [dnlib.DotNet.ModuleDefMD]::Load($DllPath)
# Use a generic HashSet<string> to hold unique literals (avoids the
# PowerShell hashtable key-pollution bug we hit earlier).
$strings = New-Object 'System.Collections.Generic.HashSet[string]'

function AddStr([string]$s) {
    if ($null -ne $s -and $s.Length -gt 0) {
        [void]$strings.Add($s)
    }
}

try {
    foreach ($type in $mod.GetTypes()) {
        # 1) Field constant strings (e.g. private const string PASSWORD = "...").
        foreach ($field in $type.Fields) {
            if ($field.HasConstant -and $null -ne $field.Constant -and $null -ne $field.Constant.Value) {
                if ($field.Constant.Value -is [string]) {
                    AddStr($field.Constant.Value)
                }
            }
        }
        # 2) ldstr operands inside method bodies (the common case for assignments).
        foreach ($method in $type.Methods) {
            if (-not $method.HasBody) { continue }
            foreach ($instr in $method.Body.Instructions) {
                if ($instr.OpCode.OperandType -eq [dnlib.DotNet.Emit.OperandType]::InlineString) {
                    $operand = $instr.Operand
                    if ($operand -is [string]) {
                        AddStr($operand)
                    }
                }
            }
        }
    }
}
finally {
    $mod.Dispose()
}

# Write results (one per line, UTF-8, no BOM).
$strings | Out-File -FilePath $OutFile -Encoding utf8
Write-Host ("Extracted {0} unique string literals from {1}" -f $strings.Count, $DllPath)
