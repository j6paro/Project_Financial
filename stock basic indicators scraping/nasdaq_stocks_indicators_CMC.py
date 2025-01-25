# 출처가 https://companiesmarketcap.com/ 인 경우

import yfinance as yf
from tqdm import tqdm
import pandas as pd
import numpy as np
from datetime import datetime
import time
import threading
import os
import requests

### 변수들 모음

# 미국 주식들 시가총액에 따른 순위 엑셀 다운로드
url = "https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/?download=csv"  # 다운로드받을 csv 파일 주소
filename = "us_stocks.csv"  # 넷상에서 다운받은 주식 목록 파일명

# User-Agent 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # User-Agent 설정. 스팸봇으로 오해하지 않도록
header = {"User-Agent": user_agent}  # 요청 헤더 설정

# 상수(파일 저장 경로 같은) 등 모음
DIR_STOCK_US = "C:/coding/DA/재테크/미국기업목록/us_stocks.csv"  # 기업 목록 저장
DIR_STOCK_INDICATOR = "C:/coding/DA/재테크/stocks_basic_indicators_CMC.xlsx"  # 작업 후 다 만들어진 파일 저장할 경로
lock = threading.Lock()  # 락
start_time = time.time()  # 시작 시간
num_cpu = os.cpu_count()  # 일 나눠서할 cpu 개수
cnt_stock_lists = os.path.isfile(
    DIR_STOCK_US
)  # 기업 목록 저장된 엑셀파일이 로컬 파일에 잘 저장됐는지 확인

# 날짜 관련
now = datetime.now()  # 오늘 날짜 가져오기
today = str(now).split()[0]  # 긴 형식의 날짜 ex) 2024-10-27 (2024년 10월 27일)

# User-Agent 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # User-Agent 설정. 스팸봇으로 오해하지 않도록
header = {"User-Agent": user_agent}  # 요청 헤더 설정

# 스레드로 데이터프레임 따로 작업한 후 concat할 데이터프레임 모아놓는 리스트들
list_dfs = list()


### 함수들 모음
# 기업목록 csv 파일 다운로드
def download_stock_list():
    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()

        # 파일 저장
        with open(DIR_STOCK_US, "wb") as f:
            f.write(response.content)
            print("기업 목록 다운로드 완료")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error 발생: {e}")

    except Exception as e:
        print(f"다운로드 중 오류 발생: {e}")


# 각 주식 지표 데이터 가져오기(기업들 PER, PBR, ROE, EPS, 영업이익 가져오기)
def add_stock_info(data):
    global cnt
    data_reset = data.reset_index(drop=True)
    for i in tqdm(range(len(data_reset))):  # 2024/04/10(수) 추가
        try:  # 해당 값들이 있는 경우에만 가져오기
            # yfinance를 사용하여 주식 데이터를 가져오기
            symbol = data_reset.loc[i]["Symbol"]
            stock_data = yf.Ticker(symbol)  # ticker.upper() 오류
            income_statement = (
                stock_data.financials
            )  # 재무제표에서 영업이익 가져오기. Financial Statement
            stock_info = stock_data.info
            # PER(주가수익비율) 정보 가져오기
            data_reset.loc[i, "PER"] = stock_info.get("forwardPE", 0)
            # PBR(주가순자산비율) 정보 가져오기
            data_reset.loc[i, "PBR"] = stock_info.get("priceToBook", 0)
            # ROE(자기자본이익률) 정보 가져오기
            data_reset.loc[i, "ROE"] = stock_info.get("returnOnEquity", 0)
            # EPS(주당순이익) 정보 가져오기
            data_reset.loc[i, "EPS"] = stock_info.get("trailingEps", 0)
            # 가장 최근 년도 영업이익 가져오기
            if len(income_statement.loc["Operating Income"]) >= 1:
                data_reset.loc[i, "OperatingIncome1"] = income_statement.loc[
                    "Operating Income"
                ][0]
                # 가장 최근 년도 -1년 영업이익 가져오기
            if len(income_statement.loc["Operating Income"]) >= 2:
                data_reset.loc[i, "OperatingIncome2"] = income_statement.loc[
                    "Operating Income"
                ][1]
        except Exception as e:
            # print(f"에러 심볼 : {symbol}") # 디버깅용
            continue

        # 기본 지표들 평가
        if (
            data_reset.loc[i, "OperatingIncome1"]
            and data_reset.loc[i, "OperatingIncome2"]
        ):  # 작년, 재작년 영업이익이 존재하는 경우
            data_reset.loc[i, "OIIR"] = (
                data_reset.loc[i, "OperatingIncome1"]
                / data_reset.loc[i, "OperatingIncome2"]
            )  # Operating Income Increasing Ratio. 영업이익 상승 비율
            if (
                data_reset.loc[i, "OIIR"] >= 1.05
            ):  # 영업이익 소폭 증가 주식 판별. 영업이익 5% 상승 기준
                data_reset.loc[i, "LROI"] = True
                data_reset.loc[i, "평가충족"] += 1
            if (
                data_reset.loc[i, "OIIR"] >= 1.10
            ):  # 영업이익 대폭 증가 주식 판별. 영업이익 10% 상승 기준
                data_reset.loc[i, "HROI"] = True
                data_reset.loc[i, "평가충족"] += 1
        if (
            data_reset.loc[i, "PER"]
            and (type(data_reset.loc[i, "PER"]) != str)
            and (data_reset.loc[i, "PER"] <= 9)  # PER만 자꾸 str이 있다고 떠서...
        ):  # 저PER 주식 판별 및 추가. PER 9 기준
            data_reset.loc[i, "LPER"] = True
            data_reset.loc[i, "평가충족"] += 1
        if data_reset.loc[i, "PBR"] and (
            data_reset.loc[i, "PBR"] <= 1.5
        ):  # 저PBR 주식 판별 및 추가. PBR 1.5 기준
            data_reset.loc[i, "LPBR"] = True
            data_reset.loc[i, "평가충족"] += 1
        if data_reset.loc[i, "ROE"] and (
            data_reset.loc[i, "ROE"] >= 0.07
        ):  # 고ROE 주식 판별 및 추가. ROE 7% 기준
            data_reset.loc[i, "HROE"] = True
            data_reset.loc[i, "평가충족"] += 1
        if data_reset.loc[i, "EPS"] and (
            data_reset.loc[i, "EPS"] >= 5
        ):  # 고EPS 주식 판별 및 추가. EPS 5 기준
            data_reset.loc[i, "HEPS"] = True
            data_reset.loc[i, "평가충족"] += 1

    lock.acquire()
    list_dfs.append(data_reset.reset_index(drop=True))
    lock.release()


# 파일 저장
def save_df():
    df_all = pd.concat(
        list_dfs, ignore_index=True
    )  # 각 스레드가 작업 끝낸 데이터프레임 합쳐주기
    if os.path.isfile(DIR_STOCK_INDICATOR):
        df_nasdaq_indicators = pd.read_excel(
            DIR_STOCK_INDICATOR, index_col=0
        )  # 이미 저장된 나스닥 기본지표 파일
        df_nasdaq_indicators = pd.concat(
            [df_nasdaq_indicators, df_all], ignore_index=True
        )  # concat 하면서 기존 index는 무시하고 초기화한다.
        df_nasdaq_indicators.to_excel(DIR_STOCK_INDICATOR, index=True, index_label="No")
    else:
        df_all.to_excel(DIR_STOCK_INDICATOR, index=True, index_label="No")

    print("저장이 완료되었습니다.")  # 저장 완료 문구


# 시간 체크
def check_time():
    global start_time
    runningtime = int(time.time() - start_time)  # 현재 시간 - 시작 시간
    runningtime_hour = runningtime // 3600  # 시간
    runningtime -= runningtime_hour * 3600
    runningtime_minute = runningtime // 60  # 분
    runningtime -= runningtime_minute * 60
    runningtime_second = runningtime  # 초
    print(f"실행시간 {runningtime_hour}:{runningtime_minute}:{runningtime_second}")


# 주식 지표들 저장할 데이터프레임 생성
def make_df():
    df_stocks_nyse = pd.read_csv(
        DIR_STOCK_US, index_col=0
    )  # 시가총액순 기업들을 df_stocks라는 이름의 DataFrame에 저장
    df_stocks_nyse = df_stocks_nyse.assign(
        DATE=today,
        PER=0,
        PBR=0,
        ROE=0,
        EPS=0,
        OperatingIncome1=0,
        OperatingIncome2=0,
        # 6개 평가 항목
        평가충족=0,
        LPER=False,  # Low PER. 낮은 PER
        LPBR=False,  # Low PBR. 낮은 PBR
        HROE=False,  # High ROE. 높은 ROE
        HEPS=False,  # High EPS. 높은 EPS
        LROI=False,  # Low Rise Of Income. 영업이익 소폭 증가
        HROI=False,  # High Rise of Income
        OIIR=False,  # 전 영업이익/전전 영업이익 = 영업이익 상승률
        소감="'-",
    )  # DataFrane에 PER, PBR, ROE, EPS 컬럼 추가 + 영업이익, 소감 추가
    return df_stocks_nyse


# 멀티 쓰레딩
def multi_thread():
    df_stocks_nyse = make_df()
    ranges = np.array_split(
        np.array(list(df_stocks_nyse.index)), num_cpu
    )  # 각 쓰레드에 할당하기 위해 종목들 스플릿하기
    thread_list = []  # 실행시킬 쓰레드들 목록
    df_stocks_for_thread = []  # 미국주식 목록 데이터프레임 쪼개서 담을 리스트

    for c in range(1, num_cpu + 1):
        globals()[f"df_stocks_split{c}"] = df_stocks_nyse.loc[
            ranges[c - 1][0] : ranges[c - 1][-1] + 1
        ]
        df_stocks_for_thread.append(eval(f"df_stocks_split{c}"))

    # 멀티쓰레딩 수행
    for d in df_stocks_for_thread:  # d는 dataframe
        t = threading.Thread(
            target=add_stock_info,
            args=(d,),
        )
        thread_list.append(t)

    for t1 in thread_list:
        t1.start()

    for t2 in thread_list:
        t2.join()


if __name__ == "__main__":
    if (not cnt_stock_lists) or (
        now.month % 2 == 0
    ):  # 기업 리스트 파일이 없거나, 짝수 달이라면 기업 목록 CSV 파일 다운로드
        download_stock_list()

    multi_thread()  # 멀티 쓰레딩

    save_df()  # 데이터프레임 엑셀로 저장

    check_time()  # 실행시간 출력
