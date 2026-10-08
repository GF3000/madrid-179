# Exporta un .pptx a PDF con PowerPoint (COM). Uso: powershell -File infra/scripts/pptx_a_pdf.ps1 <entrada.pptx> <salida.pdf>
param([string]$Entrada, [string]$Salida)
$in = (Resolve-Path $Entrada).Path
$out = [System.IO.Path]::GetFullPath($Salida)
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($in, $true, $false, $false)  # solo lectura, sin título, sin ventana
    $pres.SaveAs($out, 32)                                         # 32 = ppSaveAsPDF
    $pres.Close()
    Write-Output "ok: $out"
} finally {
    $app.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) | Out-Null
}
