import pandas as pd
import json
import argparse

# レスポンスボディからトークン数、ユーザー名、モデル名を抽出する関数
def extract_tokens_username_and_model(row):
    # 初期値の設定
    completion_tokens = float('nan')
    prompt_tokens = float('nan')
    preferred_username = float('nan')
    model_name = float('nan')
    
    # completion_tokens、prompt_tokens、およびmodelの抽出
    try:
        json_data = json.loads(row['ResponseBody'])
        completion_tokens = json_data['usage']['completion_tokens']
        prompt_tokens = json_data['usage']['prompt_tokens']
        model_name = json_data['model']
    except Exception as e:
        pass

    # preferred_usernameの抽出
    try:
        trace_records = json.loads(row['TraceRecords'])
        preferred_username = trace_records[0]['message']
    except Exception as e:
        pass

    return pd.Series([completion_tokens, prompt_tokens, preferred_username, model_name])


def main(input_file, output_file, endpoint):
    # CSVファイルを読み込む
    df = pd.read_csv(input_file, encoding='utf-8')

    # URLとレスポンスコードでフィルタリング
    filtered_df = df[(df['Url'] == endpoint) & (df['ResponseCode'] == 200)]

    # 各行に対して関数を適用して新しい列を追加
    filtered_df[['completion_tokens', 'prompt_tokens', 'preferred_username', 'model_name']] = filtered_df.apply(extract_tokens_username_and_model, axis=1)

    # データを集計してCSVファイルに保存
    aggregation = filtered_df.groupby(['ApimSubscriptionId', 'preferred_username', 'model_name']) \
    .agg({
        'completion_tokens': 'sum', 
        'prompt_tokens': 'sum',
        'Url': 'count'
    }) \
    .rename(columns={'Url': 'api_call_count'})

    aggregation.to_csv(output_file)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="サブスクリプションキー、ユーザー、モデル、および地域ごとにトークン数を集計した結果をCSVファイルに出力するプログラム")
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_file", type=str, required=True)
    parser.add_argument("--endpoint", type=str, required=True)
    
    args = parser.parse_args()

    main(args.input_file, args.output_file, args.endpoint)
