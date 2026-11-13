# Genera caras nuevas de BMO en el mismo estilo de las existentes (800x600, fondo menta, tinta oscura).
# Uso (Windows PowerShell):  powershell -File tools\generate_faces.ps1
Add-Type -AssemblyName System.Drawing

$W = 800; $H = 600
$BG    = [System.Drawing.Color]::FromArgb(128, 230, 209)
$INK   = [System.Drawing.Color]::FromArgb(33, 31, 32)
$FADE  = [System.Drawing.Color]::FromArgb(84, 178, 160)
$TONGUE= [System.Drawing.Color]::FromArgb(96, 196, 172)
$TEAR  = [System.Drawing.Color]::FromArgb(120, 190, 235)
$OutDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'faces'

# ---------- helpers ----------
function Begin-Face($bg) {
    $script:bmp = New-Object System.Drawing.Bitmap $W, $H
    $script:g = [System.Drawing.Graphics]::FromImage($script:bmp)
    $script:g.SmoothingMode = 'AntiAlias'
    $script:g.Clear($bg)
}
function Save-Face($name) {
    $path = Join-Path $OutDir "$name.png"
    $script:bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    $script:g.Dispose(); $script:bmp.Dispose()
    Write-Host "OK  $path"
}
function Pen($w, $color = $INK) {
    $p = New-Object System.Drawing.Pen $color, $w
    $p.StartCap = 'Round'; $p.EndCap = 'Round'; $p.LineJoin = 'Round'
    return $p
}
function Brush($color = $INK) { return New-Object System.Drawing.SolidBrush $color }
function Dot($cx, $cy, $rx, $ry, $color = $INK) {
    $script:g.FillEllipse((Brush $color), [single]($cx - $rx), [single]($cy - $ry), [single](2 * $rx), [single](2 * $ry))
}
function Line($x1, $y1, $x2, $y2, $w, $color = $INK) {
    $script:g.DrawLine((Pen $w $color), [single]$x1, [single]$y1, [single]$x2, [single]$y2)
}
# Curva tipo sonrisa: depth > 0 curva hacia abajo (sonrisa), depth < 0 hacia arriba (ceno / ojo feliz ^)
function Curve($cx, $y, $hw, $depth, $w, $color = $INK) {
    $d = $depth * 4 / 3
    $script:g.DrawBezier((Pen $w $color), [single]($cx - $hw), [single]$y, [single]($cx - $hw / 2), [single]($y + $d),
        [single]($cx + $hw / 2), [single]($y + $d), [single]($cx + $hw), [single]$y)
}
function Arc($cx, $cy, $r, $start, $sweep, $w, $color = $INK) {
    $script:g.DrawArc((Pen $w $color), [single]($cx - $r), [single]($cy - $r), [single](2 * $r), [single](2 * $r), [single]$start, [single]$sweep)
}
function RoundRectPath($x, $y, $w, $h, $r) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $d = 2 * $r
    $p.AddArc($x, $y, $d, $d, 180, 90)
    $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90)
    $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure()
    return $p
}
function FillRound($x, $y, $w, $h, $r, $color = $INK) {
    $script:g.FillPath((Brush $color), (RoundRectPath $x $y $w $h $r))
}
function Heart($cx, $cy, $s) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $p.AddBezier([single]$cx, [single]($cy + 0.95 * $s), [single]($cx - 0.55 * $s), [single]($cy + 0.55 * $s), [single]($cx - $s), [single]($cy + 0.1 * $s), [single]($cx - $s), [single]($cy - 0.3 * $s))
    $p.AddBezier([single]($cx - $s), [single]($cy - 0.3 * $s), [single]($cx - $s), [single]($cy - 0.85 * $s), [single]($cx - 0.2 * $s), [single]($cy - 1.0 * $s), [single]$cx, [single]($cy - 0.4 * $s))
    $p.AddBezier([single]$cx, [single]($cy - 0.4 * $s), [single]($cx + 0.2 * $s), [single]($cy - 1.0 * $s), [single]($cx + $s), [single]($cy - 0.85 * $s), [single]($cx + $s), [single]($cy - 0.3 * $s))
    $p.AddBezier([single]($cx + $s), [single]($cy - 0.3 * $s), [single]($cx + $s), [single]($cy + 0.1 * $s), [single]($cx + 0.55 * $s), [single]($cy + 0.55 * $s), [single]$cx, [single]($cy + 0.95 * $s))
    $script:g.FillPath((Brush $INK), $p)
}
function ZLetter($x, $y, $s, $w) {
    $pts = [System.Drawing.PointF[]]@(
        (New-Object System.Drawing.PointF $x, $y),
        (New-Object System.Drawing.PointF ($x + $s), $y),
        (New-Object System.Drawing.PointF $x, ($y + $s)),
        (New-Object System.Drawing.PointF ($x + $s), ($y + $s)))
    $script:g.DrawLines((Pen $w), $pts)
}
function XMark($cx, $cy, $r, $w) {
    Line ($cx - $r) ($cy - $r) ($cx + $r) ($cy + $r) $w
    Line ($cx - $r) ($cy + $r) ($cx + $r) ($cy - $r) $w
}
function Teardrop($cx, $cy, $r, $color) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $p.AddBezier([single]$cx, [single]($cy - 2.2 * $r), [single]($cx + 0.2 * $r), [single]($cy - 1.2 * $r), [single]($cx + $r), [single]($cy - 0.6 * $r), [single]($cx + $r), [single]$cy)
    $p.AddArc([single]($cx - $r), [single]($cy - $r), [single](2 * $r), [single](2 * $r), 0, 180)
    $p.AddBezier([single]($cx - $r), [single]$cy, [single]($cx - $r), [single]($cy - 0.6 * $r), [single]($cx - 0.2 * $r), [single]($cy - 1.2 * $r), [single]$cx, [single]($cy - 2.2 * $r))
    $script:g.FillPath((Brush $color), $p)
}
# Cajas de progreso (igual que bmo_connection.jpg)
function Boxes($filled) {
    for ($i = 0; $i -lt 5; $i++) {
        $x = 140 + $i * 102; $y = 510
        if ($i -lt $filled) { $script:g.FillRectangle((Brush $INK), $x, $y, 82, 27) }
        else { $script:g.DrawRectangle((Pen 3 $INK), $x, $y, 82, 27) }
    }
}

# ---------- fuente pixelada 5x7 (como bmo_wait.jpg) ----------
$FONT = @{
    'A' = '01110','10001','10001','11111','10001','10001','10001'
    'D' = '11110','10001','10001','10001','10001','10001','11110'
    'E' = '11111','10000','10000','11110','10000','10000','11111'
    'G' = '01110','10001','10000','10111','10001','10001','01111'
    'I' = '01110','00100','00100','00100','00100','00100','01110'
    'L' = '10000','10000','10000','10000','10000','10000','11111'
    'N' = '10001','11001','10101','10011','10001','10001','10001'
    'O' = '01110','10001','10001','10001','10001','10001','01110'
    'R' = '11110','10001','10001','11110','10100','10010','10001'
    'T' = '11111','00100','00100','00100','00100','00100','00100'
    'Y' = '10001','10001','01010','00100','00100','00100','00100'
    'X' = '10001','10001','01010','00100','01010','10001','10001'
    '.' = '00000','00000','00000','00000','00000','00000','00100'
}
function Pixel-Width($text, $cell) {
    $n = 0
    foreach ($ch in $text.ToCharArray()) { if ($ch -eq ' ') { $n += 4 } else { $n += 6 } }
    return ($n - 1) * $cell
}
function Pixel-Text($text, $y, $cell, $color) {
    $script:g.SmoothingMode = 'None'
    $br = Brush $color
    $x = [int](($W - (Pixel-Width $text $cell)) / 2)
    foreach ($ch in $text.ToCharArray()) {
        if ($ch -eq ' ') { $x += 4 * $cell; continue }
        $rows = $FONT[[string]$ch]
        for ($r = 0; $r -lt 7; $r++) {
            for ($c = 0; $c -lt 5; $c++) {
                if ($rows[$r][$c] -eq '1') { $script:g.FillRectangle($br, $x + $c * $cell, $y + $r * $cell, $cell, $cell) }
            }
        }
        $x += 6 * $cell
    }
    $script:g.SmoothingMode = 'AntiAlias'
}

# Geometria base tomada de bmo_happy.jpg: ojos en (250,122) y (536,122), sonrisa centrada en x=400, y~214
$EX1 = 250; $EX2 = 536; $EY = 122

# 1. blink: ojos cerrados como lineas (para parpadeo entre happy y blink)
Begin-Face $BG
Line ($EX1 - 20) $EY ($EX1 + 20) $EY 8
Line ($EX2 - 20) $EY ($EX2 + 20) $EY 8
Curve 400 214 108 34 7
Save-Face 'bmo_blink'

# 2. sleeping: ojos cerrados curvos, boquita, Zzz
Begin-Face $BG
Curve $EX1 140 28 12 7
Curve $EX2 140 28 12 7
Dot 400 250 16 12
ZLetter 560 170 26 7
ZLetter 612 108 36 8
ZLetter 668 36 50 9
Save-Face 'bmo_sleeping'

# 3. surprised: ojos grandes, cejas, boca "O"
Begin-Face $BG
Dot $EX1 118 17 28
Dot $EX2 118 17 28
Curve $EX1 70 36 (-14) 6
Curve $EX2 70 36 (-14) 6
Dot 400 262 30 40
Save-Face 'bmo_surprised'

# 4. laughing: ojos ^ ^ y boca abierta con lengua
Begin-Face $BG
Curve $EX1 142 30 (-26) 8
Curve $EX2 142 30 (-26) 8
$mouth = New-Object System.Drawing.Drawing2D.GraphicsPath
$mouth.AddLine(300, 205, 500, 205)
$mouth.AddBezier(500, 205, 492, 300, 450, 332, 400, 332)
$mouth.AddBezier(400, 332, 350, 332, 308, 300, 300, 205)
$mouth.CloseFigure()
$g.FillPath((Brush $INK), $mouth)
$g.SetClip($mouth)
Dot 400 335 62 44 $TONGUE
$g.ResetClip()
Save-Face 'bmo_laughing'

# 5. love: ojos de corazon
Begin-Face $BG
Heart $EX1 128 38
Heart $EX2 128 38
Curve 400 220 112 38 7
Save-Face 'bmo_love'

# 6. sad: ojos, cejas inclinadas, boca hacia abajo, lagrima
Begin-Face $BG
Dot $EX1 132 13.5 15
Dot $EX2 132 13.5 15
Line ($EX1 - 34) 84 ($EX1 + 30) 62 7
Line ($EX2 + 34) 84 ($EX2 - 30) 62 7
Curve 400 282 96 (-34) 7
Teardrop ($EX2 + 8) 190 11 $TEAR
Save-Face 'bmo_sad'

# 7. game: control de videojuegos (para el modo juego / Pegasus)
Begin-Face $BG
FillRound 215 168 112 34 17      # gatillo izq
FillRound 473 168 112 34 17      # gatillo der
FillRound 170 195 460 170 85     # cuerpo
Dot 232 360 72 98                # agarre izq
Dot 568 360 72 98                # agarre der
# cruceta
FillRound 266 262 26 82 6 $BG
FillRound 238 290 82 26 6 $BG
# botones
Dot 512 292 22 22 $BG
Dot 568 262 22 22 $BG
# start / select
Line 372 300 392 300 12 $BG
Line 412 300 432 300 12 $BG
Save-Face 'bmo_game'

# 8. offline: ondas apagadas con X (para errores de conexion con el servicio de voz)
Begin-Face $BG
$radii = 70, 140, 210, 285; $widths = 14, 20, 26, 32
for ($i = 0; $i -lt 4; $i++) { Arc 250 270 $radii[$i] (-42) 84 $widths[$i] $FADE }
XMark 580 270 62 26
Boxes 0
Save-Face 'bmo_offline'

# 9. loading: 4 cuadros de animacion (n cajas llenas)
for ($n = 1; $n -le 4; $n++) {
    Begin-Face $BG
    Pixel-Text 'LOADING' 190 17 $INK
    Boxes $n
    Save-Face "bmo_loading$n"
}

# 10. error: pantalla oscura estilo bmo_wait
Begin-Face $INK
Pixel-Text 'ERROR' 150 24 $BG
Pixel-Text 'TRY AGAIN' 360 11 $BG
Save-Face 'bmo_error'

# ---------- BOCAS PARA HABLAR (sincronizacion con el audio) ----------
# Mismos ojos y sonrisa que bmo_happy para que no haya "saltos" al empezar/terminar de hablar.
# Niveles por apertura (el codigo los elige segun el volumen del audio):
#   mouth_0 cerrada | mouth_1 poco abierta | mouth_2 / mouth_o / mouth_e media (variantes) | mouth_3 muy abierta
#
# Todas las bocas abiertas nacen de la misma sonrisa (comisuras a la altura de la sonrisa de
# bmo_happy), asi el paso cerrada -> abierta -> cerrada se ve continuo y no "salta" de tamano.
$TEETH = [System.Drawing.Color]::FromArgb(236, 252, 247)
$MOUTH_TOP = 212   # altura de las comisuras

# Boca abierta: borde superior = sonrisa (con $sag de curva), borde inferior = curva de $depth.
# $tongueSize: tamano relativo de la lengua (0 = sin lengua). $teethH: alto de la franja de dientes (0 = sin dientes).
function TalkMouth($hw, $sag, $depth, $tongueSize, $teethH) {
    $cx = 400; $top = $MOUTH_TOP
    $s = $sag * 4 / 3; $d = $depth * 4 / 3
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $p.AddBezier([single]($cx - $hw), [single]$top, [single]($cx - $hw * 0.5), [single]($top + $s),
        [single]($cx + $hw * 0.5), [single]($top + $s), [single]($cx + $hw), [single]$top)
    $p.AddBezier([single]($cx + $hw), [single]$top, [single]($cx + $hw * 0.92), [single]($top + $d),
        [single]($cx - $hw * 0.92), [single]($top + $d), [single]($cx - $hw), [single]$top)
    $p.CloseFigure()
    $script:g.FillPath((Brush $INK), $p)
    $script:g.SetClip($p)
    if ($teethH -gt 0) {
        # Franja de dientes que sigue la curva del labio superior
        $tp = New-Object System.Drawing.Drawing2D.GraphicsPath
        $tp.AddBezier([single]($cx - $hw), [single]$top, [single]($cx - $hw * 0.5), [single]($top + $s),
            [single]($cx + $hw * 0.5), [single]($top + $s), [single]($cx + $hw), [single]$top)
        $tp.AddBezier([single]($cx + $hw), [single]($top + $teethH), [single]($cx + $hw * 0.5), [single]($top + $s + $teethH),
            [single]($cx - $hw * 0.5), [single]($top + $s + $teethH), [single]($cx - $hw), [single]($top + $teethH))
        $tp.CloseFigure()
        $script:g.FillPath((Brush $TEETH), $tp)
    }
    if ($tongueSize -gt 0) {
        $bottom = $top + $depth
        Dot ($cx + 6) ($bottom + $depth * 0.08) ($hw * 0.55 * $tongueSize) ($depth * 0.42 * $tongueSize) $TONGUE
    }
    $script:g.ResetClip()
    # Contorno con uniones redondas: comisuras suaves, mismo grosor que la sonrisa cerrada
    $script:g.DrawPath((Pen 7), $p)
}

# Boca en "O": ovalo redondeado con lengua al fondo
function TalkO($hw, $hh, $cy) {
    $p = New-Object System.Drawing.Drawing2D.GraphicsPath
    $p.AddEllipse([single](400 - $hw), [single]($cy - $hh), [single](2 * $hw), [single](2 * $hh))
    $script:g.FillPath((Brush $INK), $p)
    $script:g.SetClip($p)
    Dot 404 ($cy + $hh * 0.95) ($hw * 0.75) ($hh * 0.45) $TONGUE
    $script:g.ResetClip()
}

function Talk-Eyes {
    Dot $EX1 $EY 13.5 15
    Dot $EX2 $EY 13.5 15
}

#                                  hw  sag depth tongue teeth
Begin-Face $BG; Talk-Eyes; Curve 400 214 108 34 7;              Save-Face 'bmo_mouth_0'   # cerrada (= happy)
Begin-Face $BG; Talk-Eyes; TalkMouth  96  22   40   0     0;    Save-Face 'bmo_mouth_1'   # entreabierta
Begin-Face $BG; Talk-Eyes; TalkMouth  88  16   72   0.9   0;    Save-Face 'bmo_mouth_2'   # "a" media
Begin-Face $BG; Talk-Eyes; TalkO      48  50   262;             Save-Face 'bmo_mouth_o'   # "o / u"
Begin-Face $BG; Talk-Eyes; TalkMouth 106  20   60   0.7   19;   Save-Face 'bmo_mouth_e'   # "e / i" ancha con dientes
Begin-Face $BG; Talk-Eyes; TalkMouth  92  12  118   1.0   18;   Save-Face 'bmo_mouth_3'   # "A" muy abierta
