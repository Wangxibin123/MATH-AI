# run.ps1 －－ Math-Copilot bootstrap for Windows
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
CD $ScriptDir # Ensure script runs from its directory initially, then CD to project root if needed (assuming script is in root)

Write-Host "===> 1. 检查 Python 3.11+"
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    Write-Error "错误：未找到 Python。请先安装 Python 3.11+ 并将其添加到系统 PATH。"
    exit 1
}
Write-Host "找到 Python: $($pythonExe.Source)"
# Simple version check (can be more sophisticated)
$versionString = (python --version)
Write-Host "Python 版本: $versionString"
if ($versionString -notmatch "Python 3\.1[1-9]") {
     Write-Warning "警告：检测到的 Python 版本不是 3.11 或更高。脚本可能无法正常工作。"
     # Decide whether to exit or continue based on strictness
     # exit 1
}

Write-Host "===> 2. 安装／升级 Poetry"
$poetryExe = Get-Command poetry -ErrorAction SilentlyContinue
if (-not $poetryExe) {
    Write-Host "未找到 Poetry，正在尝试安装..."
    try {
        (Invoke-WebRequest https://install.python-poetry.org -UseBasicParsing).Content | python -
        # Attempt to find poetry again after install
        # This assumes the installer adds it to PATH for the current session or user profile needs reload
        # A robust way might involve adding $HOME\\.local\\bin to $env:PATH if installer suggests it
        $poetryExe = Get-Command poetry -ErrorAction SilentlyContinue
        if (-not $poetryExe) {
             # If still not found, try explicit path (common default)
             $explicitPoetryPath = Join-Path $env:USERPROFILE ".local\bin\poetry.exe"
             if (Test-Path $explicitPoetryPath) {
                 $poetryExe = $explicitPoetryPath
                 Write-Host "使用显式路径找到 Poetry: $poetryExe"
             } else {
                 Write-Error "错误：Poetry 安装后仍未在 PATH 中找到，也未在默认路径 '$explicitPoetryPath' 找到。请手动验证 Poetry 安装并确保其在 PATH 中。"
                 exit 1
             }
        } else {
             Write-Host "Poetry 安装成功并找到: $($poetryExe.Source)"
        }
    } catch {
        Write-Error "错误：Poetry 安装失败。请检查网络连接或访问 https://python-poetry.org 获取手动安装说明。"
        Write-Error $_.Exception.Message
        exit 1
    }
} else {
     Write-Host "找到 Poetry: $($poetryExe.Source)"
}
# Use '&' call operator if $poetryExe is a path string
& $poetryExe config virtualenvs.in-project true

Write-Host "===> 3. 安装依赖 (poetry install)"
& $poetryExe install --no-interaction --sync # Use sync to ensure environment matches lock file exactly
if ($LASTEXITCODE -ne 0) { Write-Error "错误：poetry install 失败。"; exit 1 }

Write-Host "===> 4. Alembic 迁移"
& $poetryExe run alembic -c apps/gateway/alembic.ini upgrade head
if ($LASTEXITCODE -ne 0) { Write-Error "错误：Alembic 迁移失败。"; exit 1 }

Write-Host "===> 5. 运行种子脚本"
& $poetryExe run python -m scripts.seed
if ($LASTEXITCODE -ne 0) { Write-Error "错误：种子脚本运行失败。"; exit 1 }

Write-Host "===> 6. 执行 pytest"
& $poetryExe run pytest -q
if ($LASTEXITCODE -ne 0) {
    Write-Error "错误：Pytest 测试未通过！"
    exit 1
}

Write-Host "========= 🎉 全流程完成，数据库在 dev.db ========="
