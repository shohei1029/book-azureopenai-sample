# サンプル Jupyter Notebook

「Azure OpenAI Service で始める ChatGPT/LLM システム構築入門」のサンプルノートブックです。

## ノートブック構成
### 本書
- [00_DataIngest_AzureAISearch_PythonSDK.ipynb](./00_DataIngest_AzureAISearch_PythonSDK.ipynb): 提供している一連のサンプルノートブックのコンテンツを実行させるために必要な Azure AI Search の検索インデックスを作成します。
- [01_AzureAISearch_PythonSDK.ipynb](./01_AzureAISearch_PythonSDK.ipynb): Azure AI Search を使用してキーワード検索からベクトル検索、ハイブリッド検索、セマンティックハイブリッド検索までの機能を試すことができます。
- [02_RAG_AzureAISearch_PythonSDK.ipynb](./02_RAG_AzureAISearch_PythonSDK.ipynb): Azure AI Search を使用した RAG アーキテクチャを試すことができます。検索クエリ作成、検索結果取得、回答生成の 3 ステップに分けて実行します。
- [03_ReAct_ToolSelection_LangChain.ipynb](./03_ReAct_ToolSelection_LangChain.ipynb): ReAct を用いてツール選択の動作を試すことができます。サンプルコードではツールを2つ（Azure AI Search、CSVルックアップ）使用して情報を検索しています。
- [04_ReAct_BushoCafeReservationPlugins_LangChain.ipynb](./04_ReAct_BushoCafeReservationPlugins_LangChain.ipynb): 武将カフェ検索＆予約プラグインデモ。2つの異なるシステムを ChatGPT プラグインとして公開し、これを AI オーケストレーターである LangChain から呼ぶデモを構築します。
- [05_AzureAISearch_LangChain.ipynb](./05_AzureAISearch_LangChain.ipynb): LangChain を使用して Azure AI Search の検索クエリーを試すことができます。

### 基本
- [01_AzureOpenAI_completion.ipynb](./basic/01_AzureOpenAI_completion.ipynb): Azure OpenAI の Completion API を使用した様々なタスクを紹介します。
- [02_AzureOpenAI_chatcompletion.ipynb](./basic/02_AzureOpenAI_chatcompletion.ipynb): Azure OpenAI の Chat Completion API の基本的な動作を試すことができるサンプルです。
- [03_AzureOpenAI_functioncalling.ipynb](./basic/03_AzureOpenAI_functioncalling.ipynb): Azure OpenAI の Function Calling（関数呼び出し） の基本的な動作を試すことができるサンプルです。
- [04_SemanticKernel.ipynb](./basic/04_SemanticKernel.ipynb): SemanticKernel の基本的な動作を試すことができるサンプルです。

## 環境構築

サンプルコードを実行するにあたって、次の環境を準備する必要があります。本項を参考に環境準備をお願いします。


### 1. Python 3.10.11 のインストール

[Python 3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe) をダウンロードして実行します。

なお、Linux（Ubuntu）や macOS では最初から Python がインストールされておりそのまま利用可能です。ただ標準でインストールされている Python はややバージョンが古く、本書では Python 3.10.11 でコードのテストを行っているため、必要に応じて当該バージョンの Python インストールをオススメします。

### 2. Jupyter Notebook のインストール

コマンドプロンプトまたはターミナルで以下のコマンドを実行して Jupyter Notebook をインストールします。

```bash
pip install notebook
```

インストールが完了したら、Jupyter Notebook を起動するために以下のコマンドを実行します。

```bash
jupyter notebook
```

これにより、デフォルトのウェブブラウザで Jupyter の UI が開きます。

## ライセンス
ライセンスは [MIT ライセンス](../LICENSE.md)で提供されます。