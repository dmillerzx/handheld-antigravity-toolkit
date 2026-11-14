# Robocopy Media Sync & Jellyfin TMDB Metadata Generator for Dragon Ball Movies
# Sourced from E:\DBMovies\ -> \\192.168.1.74\Media\Movies\

$ErrorActionPreference = "Stop"

Write-Host "=========================================================="
Write-Host "  DRAGON BALL REGRADE UPGRADE & JELLYFIN METADATA SYNC    "
Write-Host "=========================================================="

$sourceBase = "E:\DBMovies\Dragon.Ball.Z.Movies.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM"
$destBase = "\\192.168.1.74\Media\Movies"

if (-not (Test-Path -LiteralPath $sourceBase)) {
    Write-Error "Source folder not found: $sourceBase"
    exit 1
}
if (-not (Test-Path -LiteralPath $destBase)) {
    Write-Error "Destination folder not found: $destBase"
    exit 1
}

$movies = @(
    [pscustomobject]@{
        Folder = "01.1.[DB] Movie 01 - Curse of the Blood Rubies"
        SourceFile = "Dragon.Ball.M01.Curse.Of.The.Blood.Rubies.1986.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball - Movie 01.mkv"
        Title = "Dragon Ball: Curse of the Blood Rubies"
        Year = "1986"
        TmdbId = "28549"
    },
    [pscustomobject]@{
        Folder = "02.1.[DB] Movie 02 - Sleeping Princess in Devil's Castle"
        SourceFile = "Dragon.Ball.M02.Sleeping.Princess.in.Devils.Castle.1987.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball - Movie 02.mkv"
        Title = "Dragon Ball: Sleeping Princess in Devil's Castle"
        Year = "1987"
        TmdbId = "39144"
    },
    [pscustomobject]@{
        Folder = "04.1.[DB] Movie 03 - Mystical Adventure"
        SourceFile = "Dragon.Ball.M03.Mystical.Adventure.1988.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball - Movie 03.mkv"
        Title = "Dragon Ball: Mystical Adventure"
        Year = "1988"
        TmdbId = "39145"
    },
    [pscustomobject]@{
        Folder = "08.1.[DB] Movie 04 - Path to Power"
        SourceFile = "Dragon.Ball.M04.The.Path.to.Power.10th.Anniversary.Movie.1996.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball - Movie 04.mkv"
        Title = "Dragon Ball: The Path to Power"
        Year = "1996"
        TmdbId = "39146"
    },
    [pscustomobject]@{
        Folder = "08.9.[DBZ] Movie 01 - Dead Zone"
        SourceFile = "Dragon.Ball.Z.M01.Dead.Zone.1989.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = $null
        Title = "Dragon Ball Z: Dead Zone"
        Year = "1989"
        TmdbId = "15367"
    },
    [pscustomobject]@{
        Folder = "10.0.[DBZ] Movie 02 - World's Strongest"
        SourceFile = "Dragon.Ball.Z.M02.The.Worlds.Strongest.1990.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 02.mkv"
        Title = "Dragon Ball Z: The World's Strongest"
        Year = "1990"
        TmdbId = "22675"
    },
    [pscustomobject]@{
        Folder = "10.0.[DBZ] Movie 03 - Tree of Might"
        SourceFile = "Dragon.Ball.Z.M03.The.Tree.of.Might.1990.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 03.mkv"
        Title = "Dragon Ball Z: The Tree of Might"
        Year = "1990"
        TmdbId = "22676"
    },
    [pscustomobject]@{
        Folder = "10.0.[DBZ] Movie 04 - Lord Slug"
        SourceFile = "Dragon.Ball.Z.M04.Lord.Slug.1991.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 04.mkv"
        Title = "Dragon Ball Z: Lord Slug"
        Year = "1991"
        TmdbId = "22677"
    },
    [pscustomobject]@{
        Folder = "10.1.[DBZ] Movie 05 - Cooler's Revenge"
        SourceFile = "Dragon.Ball.Z.M05.Coolers.Revenge.1991.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 05.mkv"
        Title = "Dragon Ball Z: Cooler's Revenge"
        Year = "1991"
        TmdbId = "15370"
    },
    [pscustomobject]@{
        Folder = "11.1.[DBZ] Movie 06 - Return of Cooler"
        SourceFile = "Dragon.Ball.Z.M06.The.Return.of.Cooler.1992.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 06.mkv"
        Title = "Dragon Ball Z: The Return of Cooler"
        Year = "1992"
        TmdbId = "22678"
    },
    [pscustomobject]@{
        Folder = "12.1.[DBZ] Movie 07 - Super Android 13"
        SourceFile = "Dragon.Ball.Z.M07.Super.Android.13.1992.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 07.mkv"
        Title = "Dragon Ball Z: Super Android 13!"
        Year = "1992"
        TmdbId = "22679"
    },
    [pscustomobject]@{
        Folder = "13.1.[DBZ] Movie 08 - Broly"
        SourceFile = "Dragon.Ball.Z.M08.Broly.The.Legendary.Super.Saiyan.1993.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 08.mkv"
        Title = "Dragon Ball Z: Broly - The Legendary Super Saiyan"
        Year = "1993"
        TmdbId = "15369"
    },
    [pscustomobject]@{
        Folder = "14.1.[DBZ] Movie 09 - Bojack Unbound"
        SourceFile = "Dragon.Ball.Z.M09.Bojack.Unbound.1993.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 09.mkv"
        Title = "Dragon Ball Z: Bojack Unbound"
        Year = "1993"
        TmdbId = "22680"
    },
    [pscustomobject]@{
        Folder = "16.1.[DBZ] Movie 10 - Broly Second Coming"
        SourceFile = "Dragon.Ball.Z.M10.Broly.Second.Coming.1994.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 10.mkv"
        Title = "Dragon Ball Z: Broly - Second Coming"
        Year = "1994"
        TmdbId = "22681"
    },
    [pscustomobject]@{
        Folder = "17.1.[DBZ] Movie 11 - Bio Broly"
        SourceFile = "Dragon.Ball.Z.M11.Bio.Broly.1994.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 11.mkv"
        Title = "Dragon Ball Z: Bio-Broly"
        Year = "1994"
        TmdbId = "22682"
    },
    [pscustomobject]@{
        Folder = "19.1.[DBZ] Movie 12 - Fusion Reborn"
        SourceFile = "Dragon.Ball.Z.M12.Fusion.Reborn.1995.BluRay.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 12.mkv"
        Title = "Dragon Ball Z: Fusion Reborn"
        Year = "1995"
        TmdbId = "15368"
    },
    [pscustomobject]@{
        Folder = "19.2.[DBZ] Movie 13 - Wrath of the Dragon"
        SourceFile = "Dragon.Ball.Z.M13.Wrath.of.the.Dragon.1995.WEB.REGRADE.1080p.Dual-Audio.FLAC.2.0.x264-SoM.mkv"
        OldFile = "Dragon Ball Z - Movie 13.mkv"
        Title = "Dragon Ball Z: Wrath of the Dragon"
        Year = "1995"
        TmdbId = "22683"
    }
)

$index = 0
foreach ($m in $movies) {
    $index++
    $destFolder = Join-Path $destBase $m.Folder
    if (-not (Test-Path -LiteralPath $destFolder)) {
        Write-Warning "Destination folder missing; creating: $destFolder"
        New-Item -ItemType Directory -LiteralPath $destFolder -Force | Out-Null
    }

    $destFilePath = Join-Path $destFolder $m.SourceFile
    $sourceFilePath = Join-Path $sourceBase $m.SourceFile

    Write-Host "`n[$index/$($movies.Count)] Processing: $($m.Title) ($($m.Year))"

    # 1. Copy via Robocopy with /J (unbuffered I/O) and /R:3 (retry)
    if (Test-Path -LiteralPath $sourceFilePath) {
        $sourceSize = (Get-Item -LiteralPath $sourceFilePath).Length
        $needCopy = $true

        if (Test-Path -LiteralPath $destFilePath) {
            $currentDestSize = (Get-Item -LiteralPath $destFilePath).Length
            if ($currentDestSize -eq $sourceSize) {
                Write-Host "     [OK] Destination file already present and matching source size ($([math]::Round($sourceSize/1GB, 2)) GB). Skipping copy."
                $needCopy = $false
            }
        }

        if ($needCopy) {
            Write-Host "     Copying ($([math]::Round($sourceSize/1GB, 2)) GB) via Robocopy /J /NP..."
            $roboArgs = @(
                $sourceBase,
                $destFolder,
                $m.SourceFile,
                "/J",        # Unbuffered I/O for large files
                "/R:3",      # Retry up to 3 times on lock/network jitter
                "/W:5",      # Wait 5 seconds between retries
                "/NP",       # No progress percentage flood
                "/NDL",      # No directory list
                "/NFL"       # No file list
            )
            $res = & robocopy.exe @roboArgs
            $exitCode = $LASTEXITCODE
            # Robocopy exit code: 0=no changes, 1=files copied successfully, 2=extra files, 3=files copied+extra
            if ($exitCode -gt 3) {
                Write-Error "Robocopy failed with exit code $exitCode for $($m.SourceFile)"
                continue
            }
            Write-Host "     [OK] Copy completed successfully."
        }
    } else {
        Write-Warning "Source file not found: $sourceFilePath"
        continue
    }

    # 2. Remove old low-quality file if present and new file is verified
    if ($m.OldFile) {
        $oldFilePath = Join-Path $destFolder $m.OldFile
        if (Test-Path -LiteralPath $oldFilePath) {
            # Double check new file exists and is healthy
            if (Test-Path -LiteralPath $destFilePath) {
                Remove-Item -LiteralPath $oldFilePath -Force -ErrorAction SilentlyContinue
                Write-Host "     [OK] Removed legacy low-quality file: $($m.OldFile)"
            }
        }
    }

    # 3. Generate Jellyfin movie.nfo metadata file
    $nfoPath = Join-Path $destFolder "movie.nfo"
    $nfoXml = @"
<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <title>$($m.Title)</title>
  <year>$($m.Year)</year>
  <tmdbid>$($m.TmdbId)</tmdbid>
</movie>
"@
    Set-Content -LiteralPath $nfoPath -Value $nfoXml -Encoding UTF8 -Force
    Write-Host "     [OK] Generated Jellyfin movie.nfo (TMDB ID: $($m.TmdbId))"
}

Write-Host "`n=========================================================="
Write-Host "    ALL MOVIES SYNCED & JELLYFIN METADATA PROVISIONED    "
Write-Host "=========================================================="
