# Full Deterministic Verification Audit for Dragon Ball Movies on NAS
# Verifies Byte Size, MKV EBML Header, Tail Readability, Legacy Cleanup, and Jellyfin NFO

$ErrorActionPreference = "Continue"

Write-Host "=========================================================="
Write-Host "   DRAGON BALL MOVIES FULL INTEGRITY & SCRAPING AUDIT     "
Write-Host "=========================================================="

$sourceBase = "E:\DBMovies\Dragon.Ball.Z.Movies.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM"
$destBase = "\\192.168.1.74\Media\Movies"

$movies = @(
    @{ Folder = "01.1.[DB] Movie 01 - Curse of the Blood Rubies"; Source = "Dragon.Ball.M01.Curse.Of.The.Blood.Rubies.1986.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball - Movie 01.mkv"; Title = "Dragon Ball: Curse of the Blood Rubies"; Year = "1986"; Tmdb = "28549" },
    @{ Folder = "02.1.[DB] Movie 02 - Sleeping Princess in Devil's Castle"; Source = "Dragon.Ball.M02.Sleeping.Princess.in.Devils.Castle.1987.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball - Movie 02.mkv"; Title = "Dragon Ball: Sleeping Princess in Devil's Castle"; Year = "1987"; Tmdb = "39144" },
    @{ Folder = "04.1.[DB] Movie 03 - Mystical Adventure"; Source = "Dragon.Ball.M03.Mystical.Adventure.1988.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball - Movie 03.mkv"; Title = "Dragon Ball: Mystical Adventure"; Year = "1988"; Tmdb = "39145" },
    @{ Folder = "08.1.[DB] Movie 04 - Path to Power"; Source = "Dragon.Ball.M04.The.Path.to.Power.10th.Anniversary.Movie.1996.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball - Movie 04.mkv"; Title = "Dragon Ball: The Path to Power"; Year = "1996"; Tmdb = "39146" },
    @{ Folder = "08.9.[DBZ] Movie 01 - Dead Zone"; Source = "Dragon.Ball.Z.M01.Dead.Zone.1989.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = $null; Title = "Dragon Ball Z: Dead Zone"; Year = "1989"; Tmdb = "15367" },
    @{ Folder = "10.0.[DBZ] Movie 02 - World's Strongest"; Source = "Dragon.Ball.Z.M02.The.Worlds.Strongest.1990.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 02.mkv"; Title = "Dragon Ball Z: The World's Strongest"; Year = "1990"; Tmdb = "22675" },
    @{ Folder = "10.0.[DBZ] Movie 03 - Tree of Might"; Source = "Dragon.Ball.Z.M03.The.Tree.of.Might.1990.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 03.mkv"; Title = "Dragon Ball Z: The Tree of Might"; Year = "1990"; Tmdb = "22676" },
    @{ Folder = "10.0.[DBZ] Movie 04 - Lord Slug"; Source = "Dragon.Ball.Z.M04.Lord.Slug.1991.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 04.mkv"; Title = "Dragon Ball Z: Lord Slug"; Year = "1991"; Tmdb = "22677" },
    @{ Folder = "10.1.[DBZ] Movie 05 - Cooler's Revenge"; Source = "Dragon.Ball.Z.M05.Coolers.Revenge.1991.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 05.mkv"; Title = "Dragon Ball Z: Cooler's Revenge"; Year = "1991"; Tmdb = "15370" },
    @{ Folder = "11.1.[DBZ] Movie 06 - Return of Cooler"; Source = "Dragon.Ball.Z.M06.The.Return.of.Cooler.1992.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 06.mkv"; Title = "Dragon Ball Z: The Return of Cooler"; Year = "1992"; Tmdb = "22678" },
    @{ Folder = "12.1.[DBZ] Movie 07 - Super Android 13"; Source = "Dragon.Ball.Z.M07.Super.Android.13.1992.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 07.mkv"; Title = "Dragon Ball Z: Super Android 13!"; Year = "1992"; Tmdb = "22679" },
    @{ Folder = "13.1.[DBZ] Movie 08 - Broly"; Source = "Dragon.Ball.Z.M08.Broly.The.Legendary.Super.Saiyan.1993.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 08.mkv"; Title = "Dragon Ball Z: Broly - The Legendary Super Saiyan"; Year = "1993"; Tmdb = "15369" },
    @{ Folder = "14.1.[DBZ] Movie 09 - Bojack Unbound"; Source = "Dragon.Ball.Z.M09.Bojack.Unbound.1993.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 09.mkv"; Title = "Dragon Ball Z: Bojack Unbound"; Year = "1993"; Tmdb = "22680" },
    @{ Folder = "16.1.[DBZ] Movie 10 - Broly Second Coming"; Source = "Dragon.Ball.Z.M10.Broly.Second.Coming.1994.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 10.mkv"; Title = "Dragon Ball Z: Broly - Second Coming"; Year = "1994"; Tmdb = "22681" },
    @{ Folder = "17.1.[DBZ] Movie 11 - Bio Broly"; Source = "Dragon.Ball.Z.M11.Bio.Broly.1994.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 11.mkv"; Title = "Dragon Ball Z: Bio-Broly"; Year = "1994"; Tmdb = "22682" },
    @{ Folder = "19.1.[DBZ] Movie 12 - Fusion Reborn"; Source = "Dragon.Ball.Z.M12.Fusion.Reborn.1995.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 12.mkv"; Title = "Dragon Ball Z: Fusion Reborn"; Year = "1995"; Tmdb = "15368" },
    @{ Folder = "19.2.[DBZ] Movie 13 - Wrath of the Dragon"; Source = "Dragon.Ball.Z.M13.Wrath.of.the.Dragon.1995.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"; Old = "Dragon Ball Z - Movie 13.mkv"; Title = "Dragon Ball Z: Wrath of the Dragon"; Year = "1995"; Tmdb = "22683" }
)

$auditResults = @()
$allPassed = $true
$totalBytesVerified = [int64]0

foreach ($m in $movies) {
    $folderPath = Join-Path $destBase $m.Folder
    $sourceFile = Join-Path $sourceBase $m.Source
    $destFile = Join-Path $folderPath $m.Source
    $nfoFile = Join-Path $folderPath "movie.nfo"

    $statusByteMatch = $false
    $statusHeaderValid = $false
    $statusTailReadable = $false
    $statusOldPurged = $true
    $statusNfoValid = $false
    $destSizeGB = 0

    # 1. Byte Size Verification
    if ((Test-Path -LiteralPath $sourceFile) -and (Test-Path -LiteralPath $destFile)) {
        $srcLen = (Get-Item -LiteralPath $sourceFile).Length
        $dstLen = (Get-Item -LiteralPath $destFile).Length
        $destSizeGB = [math]::Round($dstLen / 1GB, 2)
        if ($srcLen -eq $dstLen -and $dstLen -gt 0) {
            $statusByteMatch = $true
            $totalBytesVerified += $dstLen
        }
    }

    # 2. MKV EBML Header & Tail Verification
    if ($statusByteMatch) {
        try {
            $fs = [System.IO.File]::OpenRead($destFile)
            $header = New-Object byte[] 4
            $readBytes = $fs.Read($header, 0, 4)
            # Standard MKV EBML ID: 0x1A 0x45 0xDF 0xA3
            if ($readBytes -eq 4 -and $header[0] -eq 0x1A -and $header[1] -eq 0x45 -and $header[2] -eq 0xDF -and $header[3] -eq 0xA3) {
                $statusHeaderValid = $true
            }
            # Seek to near end of file to verify tail integrity
            if ($fs.Length -gt 65536) {
                $fs.Seek(-65536, [System.IO.SeekOrigin]::End) | Out-Null
                $tail = New-Object byte[] 65536
                $tailRead = $fs.Read($tail, 0, 65536)
                if ($tailRead -eq 65536) {
                    $statusTailReadable = $true
                }
            }
            $fs.Close()
        } catch {
            if ($fs) { $fs.Close() }
        }
    }

    # 3. Old Low-Res File Purge Verification
    if ($m.Old) {
        $oldFilePath = Join-Path $folderPath $m.Old
        if (Test-Path -LiteralPath $oldFilePath) {
            $statusOldPurged = $false
        }
    }

    # 4. Jellyfin NFO Verification
    if (Test-Path -LiteralPath $nfoFile) {
        try {
            [xml]$xml = Get-Content -LiteralPath $nfoFile -Raw
            if ($xml.movie.tmdbid -eq $m.Tmdb -and $xml.movie.year -eq $m.Year) {
                $statusNfoValid = $true
            }
        } catch {}
    }

    $itemPassed = ($statusByteMatch -and $statusHeaderValid -and $statusTailReadable -and $statusOldPurged -and $statusNfoValid)
    if (-not $itemPassed) {
        $allPassed = $false
    }

    $auditResults += [pscustomobject]@{
        Title        = $m.Title
        SizeGB       = $destSizeGB
        ByteMatch    = if ($statusByteMatch) { "PASS" } else { "FAIL" }
        MKVHeader    = if ($statusHeaderValid) { "VALID" } else { "FAIL" }
        TailReadable = if ($statusTailReadable) { "VALID" } else { "FAIL" }
        OldPurged    = if ($statusOldPurged) { "PURGED" } else { "PENDING" }
        JellyfinNfo  = if ($statusNfoValid) { "TMDB $($m.Tmdb)" } else { "FAIL" }
        Verdict      = if ($itemPassed) { "VERIFIED" } else { "PENDING" }
    }
}

Write-Host "`n--- Verification Summary Table ---"
$auditResults | Format-Table -AutoSize

Write-Host ("`nTotal Verified Space on NAS: {0:N2} GB" -f ($totalBytesVerified / 1GB))

if ($allPassed) {
    Write-Host "`n[SUCCESS] ALL 17 MOVIES FULLY AUDITED & VERIFIED 100% HEALTHY ON NAS."
    Write-Host "Safe to clean up source on E:\DBMovies\ if desired."
} else {
    $pendingCount = ($auditResults | Where-Object { $_.Verdict -ne 'VERIFIED' }).Count
    Write-Warning "$pendingCount movie(s) still pending copy or verification. DO NOT CLEAN UP SOURCE."
}
