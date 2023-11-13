# book-azureopenai-sample
「Azure OpenAI Serviceで始めるChatGPT/LLMシステム構築入門」のサンプルプログラムです。

## 環境構築
サンプルコードを実行するにあたって、次の環境を準備する必要があります。本項を参考に環境準備をお願いします。

1. Python 3.10以上
2. Git
3. Azure Developer CLI
4. Node.js 18 以上
5. PowerShell 7以上 (pwsh) ※Windowsユーザーのみ

### 1. Python 3.10.11 のインストール
[Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe) をダウンロードして実行します。

なお、Linux（Ubuntu）やmacOSでは最初からPythonがインストールされておりそのまま利用可能です。ただ標準でインストールされているPythonはややバージョンが古く、本書ではPython 3.10.11でコードのテストを行っているため、必要に応じて当該バージョンのPythonインストールをオススメします。

### 2. Git のインストール
[Git](https://git-scm.com/downloads) からご自分のOSをクリックしてインストーラーをダウンロードして実行します。

### 3. Azure Developer CLI のインストール
Azure Developer CLIは開発者向けのツールでローカル開発環境上のアプリケーションをAzure環境へ展開するための機能を提供しています。

ここで紹介する以外のインストール方法やトラブルシューティングについてはドキュメント（[azd](https://aka.ms/azd)）を参照してください。

#### Windows
Windows Package Manager（winget）[^1]が利用可能な場合は次のコマンドを実行します。


```powershell
winget install microsoft.azd
```

[^1]: wingetはWindows 10 1709 (ビルド 16299) 以降およびWindows 11のみで利用可能です。

#### Linux
次のコマンドを実行します。

```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

#### macOS
Homebrewを利用してインストールする方法が推奨されています。

```bash
brew tap azure/azd && brew install azd
```

### 4. Node.js 18 LTS 版のインストール
[Node.js 18 LTS](https://nodejs.org/ja/download) から LTS 版を選択し、ご自分の OS をクリックしてインストーラーをダウンロードして実行します。

### 5. PowerShell 7 のインストール (Windowsのみ)
[PowerShell 7](https://github.com/PowerShell/PowerShell) へアクセスし、ご自分の環境（x64またはx86）に合うPowerShellをダウンロードしてインストールします。Download (LTS) 列から.msiをダウンロードします。
