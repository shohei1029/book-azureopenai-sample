# book-azureopenai-sample

「Azure OpenAI Service で始める ChatGPT/LLM システム構築入門」のサンプルプログラムです。

技術評論社: https://gihyo.jp/book/2024/978-4-297-13929-2  
Amazon: https://www.amazon.co.jp/dp/4297139294/

## ディレクトリ構成

- [aoai-rag](./aoai-rag/): Azure OpenAI Service と Azure AI Search を利用して社内文章検索 (RAG)を実現するサンプルコード。第 5 章で主に利用し、第 6 章で ChatGPT プラグインを実装する際にも利用します。また、各要素の理解を深めるためにステップbyステップのノートブックも提供しています ([aoai-rag/notebooks](aoai-rag/notebooks))
- [aoai-flask-see](./aoai-flask-sse/): Azure OpenAI Service によるストリーミング処理を Flask と SSE (Server-Sent Events)を用いて実装するサンプルコード。第 8 章で利用。
- [aoai-apim](./aoai-apim/): Azure API Management を活用して Azure OpenAI Service を社内の共通基盤として利用するサンプルコード。第 9 章で利用。


## 環境構築

サンプルコードを実行するにあたって、次の環境を準備する必要があります。本項を参考に環境準備をお願いします。

1. Python 3.10 以上
2. Git
3. Azure Developer CLI
4. Node.js 18 以上
5. PowerShell 7 以上 (pwsh) ※Windows ユーザーのみ

### 1. Python 3.10.11 のインストール

[Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe) をダウンロードして実行します。

なお、Linux（Ubuntu）や macOS では最初から Python がインストールされておりそのまま利用可能です。ただ標準でインストールされている Python はややバージョンが古く、本書では Python 3.10.11 でコードのテストを行っているため、必要に応じて当該バージョンの Python インストールをオススメします。

### 2. Git のインストール

[Git](https://git-scm.com/downloads) からご自分の OS をクリックしてインストーラーをダウンロードして実行します。

### 3. Azure Developer CLI のインストール

Azure Developer CLI は開発者向けのツールでローカル開発環境上のアプリケーションを Azure 環境へ展開するための機能を提供しています。

ここで紹介する以外のインストール方法やトラブルシューティングについてはドキュメント（[azd](https://aka.ms/azd)）を参照してください。

#### Windows

Windows Package Manager（winget）[^1]が利用可能な場合は次のコマンドを実行します。

```powershell
winget install microsoft.azd
```

[^1]: winget は Windows 10 1709 (ビルド 16299) 以降および Windows 11 のみで利用可能です。

#### Linux

次のコマンドを実行します。

```bash
curl -fsSL https://aka.ms/install-azd.sh | bash
```

#### macOS

Homebrew を利用してインストールする方法が推奨されています。

```bash
brew tap azure/azd && brew install azd
```

### 4. Node.js 18 LTS 版のインストール

[Node.js 18 LTS](https://nodejs.org/ja/download) から LTS 版を選択し、ご自分の OS をクリックしてインストーラーをダウンロードして実行します。

### 5. PowerShell 7 のインストール (Windows のみ)

[PowerShell 7](https://github.com/PowerShell/PowerShell) へアクセスし、ご自分の環境（x64 または x86）に合う PowerShell をダウンロードしてインストールします。Download (LTS) 列から.msi をダウンロードします。
