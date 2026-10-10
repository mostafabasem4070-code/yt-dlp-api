# ==============================================================================
# GitHub Deployer & Cloud Sync Center - YouTube API Hub
# Repository: https://github.com/mostafabasem4070-code/yt-dlp-api
# ==============================================================================

param(
    [switch]$Gui
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "GitHub Deployer - YouTube API Hub"

$repoUrl = "https://github.com/mostafabasem4070-code/yt-dlp-api.git"
$defaultMsg = "Update YouTube API Hub: enhance cookies persistence and live telemetry"

# ------------------------------------------------------------------------------
# Native GUI Window
# ------------------------------------------------------------------------------
function Show-DeployGui {
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing
    [System.Windows.Forms.Application]::EnableVisualStyles()

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "Cloud Deploy Center | GitHub Deployer"
    $form.Size = New-Object System.Drawing.Size(650, 680)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.RightToLeft = [System.Windows.Forms.RightToLeft]::No
    $form.RightToLeftLayout = $false
    $form.BackColor = [System.Drawing.Color]::FromArgb(248, 250, 252)
    $form.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)

    # Header Panel
    $headerPanel = New-Object System.Windows.Forms.Panel
    $headerPanel.Dock = "Top"
    $headerPanel.Height = 70
    $headerPanel.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
    $form.Controls.Add($headerPanel)

    $headerTitle = New-Object System.Windows.Forms.Label
    $headerTitle.Text = "GitHub Cloud Deployer"
    $headerTitle.ForeColor = [System.Drawing.Color]::White
    $headerTitle.Font = New-Object System.Drawing.Font("Segoe UI", 12.5, [System.Drawing.FontStyle]::Bold)
    $headerTitle.Location = New-Object System.Drawing.Point(20, 12)
    $headerTitle.AutoSize = $true
    $headerPanel.Controls.Add($headerTitle)

    $headerSub = New-Object System.Windows.Forms.Label
    $headerSub.Text = "Repository: https://github.com/mostafabasem4070-code/yt-dlp-api"
    $headerSub.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
    $headerSub.Font = New-Object System.Drawing.Font("Segoe UI", 8.5)
    $headerSub.Location = New-Object System.Drawing.Point(20, 40)
    $headerSub.AutoSize = $true
    $headerPanel.Controls.Add($headerSub)

    # Content Container
    $container = New-Object System.Windows.Forms.Panel
    $container.Location = New-Object System.Drawing.Point(20, 85)
    $container.Size = New-Object System.Drawing.Size(595, 545)
    $form.Controls.Add($container)

    # Files Status Label
    $lblFiles = New-Object System.Windows.Forms.Label
    $lblFiles.Text = "Modified Files (Ready to Deploy):"
    $lblFiles.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
    $lblFiles.ForeColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $lblFiles.Location = New-Object System.Drawing.Point(0, 0)
    $lblFiles.AutoSize = $true
    $container.Controls.Add($lblFiles)

    # Files ListBox
    $txtFiles = New-Object System.Windows.Forms.TextBox
    $txtFiles.Multiline = $true
    $txtFiles.ScrollBars = "Vertical"
    $txtFiles.ReadOnly = $true
    $txtFiles.Location = New-Object System.Drawing.Point(0, 24)
    $txtFiles.Size = New-Object System.Drawing.Size(595, 80)
    $txtFiles.Font = New-Object System.Drawing.Font("Consolas", 9.0)
    $txtFiles.BackColor = [System.Drawing.Color]::FromArgb(241, 245, 249)
    $txtFiles.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
    $container.Controls.Add($txtFiles)

    $gitStat = git status --short
    if ($gitStat) {
        $txtFiles.Text = ($gitStat -join [Environment]::NewLine)
    }
    else {
        $txtFiles.Text = "No uncommitted changes (Working tree clean)."
    }

    # Commit Message Label
    $lblCommit = New-Object System.Windows.Forms.Label
    $lblCommit.Text = "Commit Message:"
    $lblCommit.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
    $lblCommit.ForeColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $lblCommit.Location = New-Object System.Drawing.Point(0, 115)
    $lblCommit.AutoSize = $true
    $container.Controls.Add($lblCommit)

    # Commit Message TextBox
    $txtCommit = New-Object System.Windows.Forms.TextBox
    $txtCommit.Location = New-Object System.Drawing.Point(0, 138)
    $txtCommit.Size = New-Object System.Drawing.Size(595, 28)
    $txtCommit.Text = $defaultMsg
    $container.Controls.Add($txtCommit)

    # Auth Method GroupBox
    $grpAuth = New-Object System.Windows.Forms.GroupBox
    $grpAuth.Text = "Authentication Method"
    $grpAuth.Location = New-Object System.Drawing.Point(0, 175)
    $grpAuth.Size = New-Object System.Drawing.Size(595, 95)
    $grpAuth.ForeColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
    $container.Controls.Add($grpAuth)

    $rbBrowser = New-Object System.Windows.Forms.RadioButton
    $rbBrowser.Text = "Browser Sign-in (Git Credential Manager - Recommended)"
    $rbBrowser.Checked = $true
    $rbBrowser.Location = New-Object System.Drawing.Point(15, 22)
    $rbBrowser.Size = New-Object System.Drawing.Size(560, 24)
    $grpAuth.Controls.Add($rbBrowser)

    $rbToken = New-Object System.Windows.Forms.RadioButton
    $rbToken.Text = "Use GitHub Personal Access Token (PAT):"
    $rbToken.Location = New-Object System.Drawing.Point(15, 55)
    $rbToken.Size = New-Object System.Drawing.Size(300, 24)
    $grpAuth.Controls.Add($rbToken)

    $txtToken = New-Object System.Windows.Forms.TextBox
    $txtToken.Location = New-Object System.Drawing.Point(320, 55)
    $txtToken.Size = New-Object System.Drawing.Size(260, 26)
    $txtToken.Enabled = $false
    $txtToken.PasswordChar = "*"
    $grpAuth.Controls.Add($txtToken)

    $rbBrowser.Add_CheckedChanged({
            $txtToken.Enabled = $rbToken.Checked
        })
    $rbToken.Add_CheckedChanged({
            $txtToken.Enabled = $rbToken.Checked
            if ($rbToken.Checked) { $txtToken.Focus() }
        })

    # Action Button
    $btnDeploy = New-Object System.Windows.Forms.Button
    $btnDeploy.Text = "Deploy to GitHub Now !"
    $btnDeploy.Location = New-Object System.Drawing.Point(0, 280)
    $btnDeploy.Size = New-Object System.Drawing.Size(595, 42)
    $btnDeploy.BackColor = [System.Drawing.Color]::FromArgb(16, 185, 129)
    $btnDeploy.ForeColor = [System.Drawing.Color]::White
    $btnDeploy.FlatStyle = "Flat"
    $btnDeploy.Font = New-Object System.Drawing.Font("Segoe UI", 10.5, [System.Drawing.FontStyle]::Bold)
    $btnDeploy.Cursor = [System.Windows.Forms.Cursors]::Hand
    $container.Controls.Add($btnDeploy)

    # Log Output Label
    $lblLog = New-Object System.Windows.Forms.Label
    $lblLog.Text = "Deployment Output (Live Console):"
    $lblLog.Font = New-Object System.Drawing.Font("Segoe UI", 9.0, [System.Drawing.FontStyle]::Bold)
    $lblLog.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
    $lblLog.Location = New-Object System.Drawing.Point(0, 332)
    $lblLog.AutoSize = $true
    $container.Controls.Add($lblLog)

    # Log Output TextBox
    $txtLog = New-Object System.Windows.Forms.TextBox
    $txtLog.Multiline = $true
    $txtLog.ScrollBars = "Vertical"
    $txtLog.ReadOnly = $true
    $txtLog.Location = New-Object System.Drawing.Point(0, 355)
    $txtLog.Size = New-Object System.Drawing.Size(595, 180)
    $txtLog.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
    $txtLog.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
    $txtLog.Font = New-Object System.Drawing.Font("Consolas", 8.8)
    $container.Controls.Add($txtLog)

    $appendLog = {
        param($msg)
        $txtLog.AppendText($msg + [Environment]::NewLine)
        $txtLog.SelectionStart = $txtLog.TextLength
        $txtLog.ScrollToCaret()
        [System.Windows.Forms.Application]::DoEvents()
    }

    $btnDeploy.Add_Click({
            $btnDeploy.Enabled = $false
            $btnDeploy.Text = "Deploying..."
            $txtLog.Clear()

            &$appendLog "[*] Starting deployment to GitHub..."

            # Check token if selected
            if ($rbToken.Checked) {
                $tok = $txtToken.Text.Trim()
                if (-not $tok) {
                    [System.Windows.Forms.MessageBox]::Show("Please enter a Personal Access Token.", "Warning", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
                    $btnDeploy.Enabled = $true
                    $btnDeploy.Text = "Deploy to GitHub Now !"
                    return
                }
                $authUrl = "https://${tok}@github.com/mostafabasem4070-code/yt-dlp-api.git"
                git remote remove origin 2>$null
                git remote add origin $authUrl
                &$appendLog "[OK] Remote configured with Personal Access Token."
            }
            else {
                git remote remove origin 2>$null
                git remote add origin $repoUrl
                &$appendLog "[OK] Remote set to browser authentication."
            }

            # git add
            &$appendLog "[*] Adding all files (git add --all)..."
            git add --all

            # git commit
            $cMsg = $txtCommit.Text.Trim()
            if (-not $cMsg) { $cMsg = $defaultMsg }
            &$appendLog "[*] Committing changes: $cMsg"
            $commitOut = git commit --allow-empty -m $cMsg 2>&1
            &$appendLog ($commitOut -join [Environment]::NewLine)

            # git push
            &$appendLog "[*] Pushing to GitHub (git push -u origin main)..."
            $pushOut = git push -u origin main 2>&1
            &$appendLog ($pushOut -join [Environment]::NewLine)

            if ($LASTEXITCODE -eq 0) {
                &$appendLog ""
                &$appendLog "================================================================="
                &$appendLog "[SUCCESS] Deployment completed successfully!"
                &$appendLog "Repository: https://github.com/mostafabasem4070-code/yt-dlp-api"
                &$appendLog "================================================================="
                [System.Windows.Forms.MessageBox]::Show("Successfully deployed to GitHub repository!", "Success", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
            }
            else {
                &$appendLog ""
                &$appendLog "[!] Push rejected or encountered conflict."
                $res = [System.Windows.Forms.MessageBox]::Show("Regular push failed. Since you only modify local files, do you want to Force Push and overwrite remote?", "Force Push Confirmation", [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
                if ($res -eq [System.Windows.Forms.DialogResult]::Yes) {
                    &$appendLog "[*] Executing force push (git push -u origin main --force)..."
                    $forceOut = git push -u origin main --force 2>&1
                    &$appendLog ($forceOut -join [Environment]::NewLine)
                    if ($LASTEXITCODE -eq 0) {
                        &$appendLog "[SUCCESS] Force push completed successfully!"
                        [System.Windows.Forms.MessageBox]::Show("Force push completed successfully!", "Success", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
                    }
                    else {
                        &$appendLog "[ERROR] Force push failed."
                        [System.Windows.Forms.MessageBox]::Show("Force push failed. Please check connection or token permissions.", "Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                    }
                }
            }

            # Refresh status
            $refreshStat = git status --short
            $txtFiles.Text = if ($refreshStat) { ($refreshStat -join [Environment]::NewLine) } else { "No uncommitted changes (Working tree clean)." }
            $btnDeploy.Enabled = $true
            $btnDeploy.Text = "Deploy to GitHub Now !"
        })

    [void]$form.ShowDialog()
}

# ------------------------------------------------------------------------------
# Prerequisites Check
# ------------------------------------------------------------------------------
$gitCheck = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCheck) {
    Write-Host "[X] Error: Git is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "    Please install Git from: https://git-scm.com" -ForegroundColor Yellow
    exit 1
}

$gitVer = (git --version).Trim()

# Auto-configure git user/email if missing to prevent silent commit failures
$gitEmail = git config --global user.email 2>$null
$gitName = git config --global user.name 2>$null
if (-not $gitEmail -or -not $gitName) {
    git config --global user.name "GitHub Deployer"
    git config --global user.email "deployer@localhost"
}

# Initialize local repo if it doesn't exist
if (-not (Test-Path ".git")) {
    git init | Out-Null
    git branch -M main | Out-Null
}

if ($Gui) {
    Show-DeployGui
    exit 0
}

# ------------------------------------------------------------------------------
# Clean Terminal Interface
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "       GitHub Deployer & Cloud Sync Center - YouTube API Hub" -ForegroundColor White
Write-Host "       Repository: https://github.com/mostafabasem4070-code/yt-dlp-api" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[OK] Git Engine: $gitVer" -ForegroundColor Green

Write-Host ""
Write-Host "[*] Modified Files & Status:" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
$currentStatus = git status --short
if ($currentStatus) {
    git status --short
}
else {
    Write-Host "    (No uncommitted changes - working tree clean)" -ForegroundColor DarkGray
}
Write-Host "------------------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

Write-Host "Select Deploy Option:" -ForegroundColor White
Write-Host " [1] Browser Sign-in (Git Credential Manager - Recommended)" -ForegroundColor Green
Write-Host " [2] Personal Access Token (PAT - ghp_...)" -ForegroundColor Yellow
Write-Host " [3] Open GUI Window" -ForegroundColor Cyan
Write-Host " [4] Cancel & Exit" -ForegroundColor Red
Write-Host ""

$choice = (Read-Host "Enter Choice [1, 2, 3, or 4] (Default: 1)").Trim()
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

if ($choice -eq "4") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}

if ($choice -eq "3") {
    Show-DeployGui
    exit 0
}

if ($choice -eq "2") {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Yellow
    Write-Host " Personal Access Token (PAT):" -ForegroundColor White
    Write-Host " Generate token with 'repo' scope at: https://github.com/settings/tokens/new" -ForegroundColor Cyan
    Write-Host "==============================================================================" -ForegroundColor Yellow
    Write-Host ""

    $token = (Read-Host "Paste your Personal Access Token here (ghp_...)").Trim()
    if ([string]::IsNullOrWhiteSpace($token)) {
        Write-Host "[X] Error: Token cannot be empty!" -ForegroundColor Red
        exit 1
    }

    $remoteWithAuth = "https://${token}@github.com/mostafabasem4070-code/yt-dlp-api.git"
    git remote remove origin 2>$null
    git remote add origin $remoteWithAuth
    Write-Host "[OK] Remote configured with Personal Access Token." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "[*] Selected browser-based sign-in." -ForegroundColor Cyan
    git remote remove origin 2>$null
    git remote add origin $repoUrl
}

# Commit message
Write-Host ""
$commitMsg = (Read-Host "Enter Commit Message [Press Enter for default]").Trim()
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = $defaultMsg
}

# Staging & Committing
Write-Host ""
Write-Host "[*] Adding all files (git add --all)..." -ForegroundColor Cyan
git add --all

Write-Host "[*] Committing changes (git commit)..." -ForegroundColor Cyan
$commitOutput = git commit --allow-empty -m $commitMsg 2>&1
Write-Host ($commitOutput -join [Environment]::NewLine) -ForegroundColor DarkGray

Write-Host ""
Write-Host "[*] Pushing to GitHub (main branch)..." -ForegroundColor Cyan
Write-Host "    If prompted, complete authentication in your browser window." -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==============================================================================" -ForegroundColor Green
    Write-Host " [OK] Successfully Deployed to GitHub!" -ForegroundColor Green
    Write-Host "     Repository: https://github.com/mostafabasem4070-code/yt-dlp-api" -ForegroundColor Yellow
    Write-Host "==============================================================================" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "[!] Push rejected because remote repository contains conflicting changes." -ForegroundColor Yellow
    $forceChoice = (Read-Host "Since you only modify local files, do you want to FORCE PUSH? (Type y to confirm or n to cancel) [y/n]").Trim().ToLower()
    if ($forceChoice -eq "y") {
        Write-Host ""
        Write-Host "[*] Executing force push (git push -u origin main --force)..." -ForegroundColor Cyan
        git push -u origin main --force
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "==============================================================================" -ForegroundColor Green
            Write-Host " [OK] Force push succeeded!" -ForegroundColor Green
            Write-Host "     Repository: https://github.com/mostafabasem4070-code/yt-dlp-api" -ForegroundColor Yellow
            Write-Host "==============================================================================" -ForegroundColor Green
        }
        else {
            Write-Host "[X] Force push failed. Please verify your token permissions and connection." -ForegroundColor Red
        }
    }
    else {
        Write-Host "Deployment cancelled." -ForegroundColor Yellow
    }
}
