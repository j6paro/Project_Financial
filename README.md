# Project_Financial
The topic of this projects is financial. It's about financial indicators scrapping, using cloud etc.

# 1. 개요

## 1) 설명
\- 미국 주식 종목 선정시 참고할 수 있는 기본 지표들을 스크래핑 하는 코드를 작성한다.  
\- 1차 목표는 수동으로 실행시키는 코드의 완성, 2차 목표는 클라우드를 활용해 배치 프로세스로 일정 주기마다 자동으로 종목의 지표들을 받아올 수 있도록 한다.

# 2. 코드
```
import yfinance as yf
from tqdm import tqdm
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import time
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import threading
import os

start_time = time.time()  # 시작 시간
# num_cpu = os.cpu_count()  # 일 나눠서할 cpu 개수
num_cpu = 6
# cnt = 0  # 모든 쓰레드가 일을 마쳤는가?

# 오늘 날짜 가져오기
now = datetime.now()
today = (
    str(now.year)[2:] + "0" + str(now.month) + str(now.day)
)  # 간소화한 날짜 ex) 241027 (2024년 10월 27일)
today2 = str(now).split()[0]  # 긴 형식의 날짜 ex) 2024-10-27 (2024년 10월 27일)

# 미국 주식들 시가총액에 따른 순위 엑셀 다운로드
url = "https://companiesmarketcap.com/usa/largest-companies-in-the-usa-by-market-cap/?download=csv"  # 다운로드받을 csv 파일 주소
filename = today + "_stocks.csv"  # 넷상에서 다운받은 주식 목록 파일명
filename_save = "stocks_basic_indicators.xlsx"  # 완성된 데이터프레임을 저장할 파일

# User-Agent 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # User-Agent 설정. 스팸봇으로 오해하지 않도록
header = {"User-Agent": user_agent}  # 요청 헤더 설정

# 파일 저장 경로 설정
DIR_STOCK_US = (
    "C:/coding/DA/재테크/미국기업목록/" + filename
)  # 인터넷상에서 기업목록 다운받기
DIR_STOCK_INDICATOR = "C:/coding/DA/재테크/"  # 작업 후 다 만들어진 파일 저장할 경로

# 락
lock = threading.Lock()


### 모듈0. 함수 모음
# 각 주식 지표 데이터 가져오기
def add_stock_info(data):
    global df_stocks
    data_reset = data.reset_index(drop=True)
    for i in tqdm(range(len(data_reset))):  # 2024/04/10(수) 추가
        # yfinance를 사용하여 주식 데이터를 가져오기
        stock_data = yf.Ticker(data_reset.loc[i]["Symbol"])
        income_statement = (
            stock_data.financials
        )  # 재무제표에서 영업이익 가져오기. Financial Statement
        try:  # 해당 값들이 있는 경우에만 가져오기
            # PER(주가수익비율) 정보 가져오기
            data_reset.loc[i, "PER"] = stock_data.info["forwardPE"]
            # PBR(주가순자산비율) 정보 가져오기
            data_reset.loc[i, "PBR"] = stock_data.info["priceToBook"]
            # ROE(자기자본이익률) 정보 가져오기
            data_reset.loc[i, "ROE"] = stock_data.info["returnOnEquity"]
            # EPS(주당순이익) 정보 가져오기
            data_reset.loc[i, "EPS"] = stock_data.info["trailingEps"]
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

        except KeyError as e:
            # 해당 항목이 없는 경우 스킵
            # print(f'주식 데이터에서 {e} 정보를 찾을 수 없어 스킵합니다.') # 240410수 사실 확인 잘 안 하는 것 같아서 스킵
            continue

    lock.acquire()
    data_reset = data_reset.reset_index(drop=True)
    make_or_edit_excel(data_reset)
    lock.release()

    """
    lock.acquire()
    result_dataframes.append(data_reset)
    lock.release()

    if len(result_dataframes) == num_cpu:
        df_stocks = df_stocks.reset_index(drop=True)
        df_stocks = pd.concat(result_dataframes, ignore_index=True)
    """


# 엑셀파일 편집, 새로 생성 또는 수정 및 저장
# stock_wb 는 stock_workbook 이라는 의미
def edit_excel(dataframe):
    stock_wb = load_workbook(
        DIR_STOCK_INDICATOR + filename_save, read_only=False, data_only=False
    )
    stock_ws = stock_wb.active
    # 보충 필요1 -> 만약 빈 엑셀이면 header=True
    # 보충 필요2 -> 만약 header=False면 빈 행 삭제하기
    for r in dataframe_to_rows(dataframe, index=True, header=False):
        stock_ws.append(r)
    stock_wb.save(DIR_STOCK_INDICATOR + filename_save)
    stock_wb.close()


def make_or_edit_excel(dataframe):
    if os.path.isfile(DIR_STOCK_INDICATOR + filename_save):
        edit_excel(dataframe)
    else:
        stock_wb = Workbook()
        stock_ws = stock_wb.active
        stock_wb.save(DIR_STOCK_INDICATOR + filename_save)
        stock_wb.close()
        edit_excel(dataframe)


if __name__ == "__main__":
    ### 모듈1. 미국기업 시가총액순 엑셀 다운로드 받기
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

    ### 모듈2. 엑셀/csv 파일 읽어서 DataFrame에 저장하고 빈 컬럼들 생성
    df_stocks = pd.read_csv(
        DIR_STOCK_US
    )  # 시가총액순 기업들을 df_stocks라는 이름의 DataFrame에 저장
    df_stocks = df_stocks.assign(
        DATE=None,
        PER=None,
        PBR=None,
        ROE=None,
        EPS=None,
        OperatingIncome1=None,
        OperatingIncome2=None,
        소감=None,
    )  # DataFrane에 PER, PBR, ROE, EPS 컬럼 추가 + 영업이익, 소감 추가

    # 영업이익1~4 컬럼 모두 0으로 채우기, 소감 -로 채우기
    for i in range(1, 3):
        df_stocks["OperatingIncome" + str(i)] = 0
    df_stocks["DATE"] = today2
    df_stocks["소감"] = "'-"

    ### 모듈3. 기업들 PER, PBR, ROE, EPS, 영업이익 가져오기

    ranges = np.array_split(np.array(list(df_stocks.index)), num_cpu)
    result_dataframes = (
        []
    )  # 미국주식 목록 데이터프레임 쪼갠 뒤, add_stock_info 함수를 거친 데이터프레임들을 다시 합쳐주기 위해 한 리스트에 모을거임.
    thread_list = []  # 실행시킬 쓰레드들 목록
    df_stocks_for_thread = []  # 미국주식 목록 데이터프레임 쪼개서 담을 리스트

    for c in range(1, num_cpu + 1):
        globals()[f"df_stocks_split{c}"] = df_stocks.loc[
            ranges[c - 1][0] : ranges[c - 1][-1] + 1
        ]
        df_stocks_for_thread.append(eval(f"df_stocks_split{c}"))

    # 모듈3_1. 멀티쓰레딩
    for d in df_stocks_for_thread:  # d는 dataframe
        # print(d) # 디버깅용
        t = threading.Thread(target=add_stock_info, args=(d,))
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    # 모듈3_3. cpu수만큼 쪼갰던 데이터프레임 다시 합치기
    ### 모듈4. 완성된 데이터프레임 엑셀 파일로 저장하기
    # 모듈 3_3, 4는 쓰레드간 속도 차이 문제로 add_stock_info 내부로 옮긴다.

    # 저장 완료 문구
    print("저장이 완료되었습니다.")

    # 실행시간 체크
    print("실행시간 : " + str(time.time() - start_time)[:5] + "초")
```
