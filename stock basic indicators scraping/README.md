# 1. 개요

## 1-1. 설명
\- 미국 주식 종목 선정시 참고할 수 있는 기본 지표들을 스크래핑 하는 코드를 작성한다.  
\- 1차 목표는 수동으로 실행시키는 코드의 완성, 2차 목표는 클라우드를 활용해 배치 프로세스로 일정 주기마다 자동으로 종목의 지표들을 받아올 수 있도록 한다.

# 2. 코드

## 2-1. 전체적인 흐름

\- (1) NYSE에서 나스닥에 상장된 전 종목 리스트 스크랩 -> (2) 각 종목에 대해 야후 파이낸스에서 PER, PBR 등 투자 기본 지표들 받아오기 -> (3) 각 지표들에 기준을 두고 저PER, 저PBR 종목 등 선별하기  
\- 각 단계에서 사용된 주요 패키지, 라이브러리는 다음과 같다.  
(1) : selenium  
(2) : yfinance  
(3) : pandas, openpyxl  

## 2-2. nasdaq_stocks_indicators_CMC.py

\- https://companiesmarketcap.com/ 에서 미국 기업 목록을 csv파일로 다운로드 받는 경우  

### 2-2-1. 라이브러리 import  
```
import yfinance as yf
from tqdm import tqdm
import pandas as pd
import numpy as np
from datetime import datetime
import time
import threading
import os
import requests
```
\- yfinance : 야후 파이낸스에서 주식 기본 지표들을 스크래핑하기 위해 import 한다. 그런데 너무 많이 스크래핑 요청을 보내다 보면 야후 파이낸스에서 이를 봇으로 감지하는지 종종 알 수 없는 이유로 스크래핑이 중간에 멈추기도 한다.  
\- tqdm : 스크래핑 진척도를 확인하기 위해 import 한다.  
\- os, pandas, numpy : 데이터프레임을 만들어 로컬 파일로 저장하기 위해 import 한다. os를 이용해 로컬 파일이 이미 있는 경우에는 불러와서 저장하고, 없으면 새로 만들어서 저장한다.  
\- datetime, time : 웹 스크래핑한 날짜를 데이터프레임의 날짜 컬럼(Date)으로 추가하기 위해 import 한다.  
\- threading : 수천 개의 종목들에 대해 스크래핑하다보니 시간이 꽤 걸린다. 멀티쓰레딩을 이용해 시간을 단축시킨다.  
\- requests : url을 이용해 기업 목록을 저장하기 위해 import 한다.  

### 2-2-2. 변수들 모음
```
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
```

### 2-2-3. 기업목록 csv 파일 다운로드
```
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
```
\- [미국 기업 목록](https://companiesmarketcap.com/) 사이트에서 기업 목록 csv 파일을 다운로드 한다.  

### 2-2-4. yfinance 이용해서 각 주식 지표 웹 스크래핑
```
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
```
\- 저장한 미국 기업 목록을 바탕으로 yfinance로 야후 파이낸스에서 기본 지표 스크래핑하고, 판별한다.  
\- 저PER 기준 : PER 9 이하  
\- 저PBR 기준 : PBR 1.5 이하  
\- 고ROE 기준 : ROE 7% 이상  
\- 고EPS 기준 : EPS 5 이상  

### 2-2-5. 주식 기본 지표 로컬 파일로 저장
```
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
```

### 2-2-6. 실행시간 출력
```
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

```
\- 실행시간이 얼마나 걸렸는지 확인한다.  

### 2-2-7. 데이터프레임 생성
```
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
```
\- 기본 지표들을 저장할 데이터프레임을 생성하는 함수

### 2-2-8. 멀티쓰레딩
```
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
```
\- CPU 수만큼 쓰레드 생성해서 시간을 효율화한다.

## 2-2. nasdaq_stocks_indicators_NYSE.py

\- selenium으로 NYSE에서 미국 기업 목록을 직접 긁어서 엑셀 파일로 만드는 경우  

# 3. 피드백

## 3-1. 추가, 수정할 것들

### 1. 241103_NYSE에서 나스닥 상장 전 종목 받아오기
\- 지금은 다음 종목들이 있는 페이지로 넘길 때 WebDriverWait(driver, 3) 이렇게 일정 시간 대기하라고 하고 있다. 하지만 [이 블로그](https://june98.tistory.com/11)에서는 일정 시간을 정한 게 아닌, 해당 요소가 화면에 표시될 때까지 대기하는 것도 가능하다.  
\-> 지금 다시 보니까 이미 내가 작성한 코드가 해당 기능을 적용한 것.
### 2. 241104_OOP 스타일로 코드 리팩토링
\- 지금은 변수, 함수들 너무 난잡하고 한 눈에 안 들어옴  
\-> 일단 OOP 스타일로 다시 정리하긴 했는데, 엄청 깔끔한 느낌은 들지 않는다. 매우 소소하게 깔끔해진 느낌? 무엇보다 챗gpt한테도 OOP 스타일로 리팩토링 해달라고 했는데 나보다 더 잘한 것 같음.  
\-> 310줄 -> 290줄로 줄이긴 함.
### 3. 241104_엑셀 생성하고 수정하는 함수의 사용 빈도, 존재 이유 생각
\- 속도에 방해되는 것 아닌가? 안정성도 떨어지는 것 같고. 그냥 데이터프레임 만들어서 파이썬 내부에서 여차저차 수정하는 게 낫지 않나? 데이터프레임 만들고 concat을 하는 게 낫지 않은가

## 3-2. 공부할 것들  

### 1. 멀티쓰레딩, 멀티프로세싱 차이
\- 나는 멀티쓰레딩 사용했는데, 멀티프로세싱과 뭐가 다른지? 각각 언제 사용해야 하는지? 스레드와 프로세스는 뭔지?
### 2. 챗gpt OOP vs 내 OOP
\- 챗gpt가 나보다 코드 줄 수를 훨씬 많이 줄였음. 비교해보자.  
### 3. stderr, redirect? 이것들 다 뭔지  
\- client404 에러는 except로 예외처리 해도 자꾸 뜨던데, 이걸 없앨 수 있는 방법이 있다.

## 3-3. 배운 것들
### 1. 프로세스 vs 스레드
\- 웹 스크랩 같은 IO 작업 많은 애들은 멀티쓰레딩이 낫다.  
### 2. 에러들 정리
\- 특정 패키지의 내부 클래스의 함수들에서 문제가 발생한 경우에도, 잘 살펴보면 원인 발견, 해결 가능  
\- 예외처리 하는 방법. Exception하면 여러 개 예외처리 가능  
\- 에러 문구도 안 뜨게 가능 : stderr 관련  
```
import yfinance as yf
import contextlib
import io

def check_symbol(symbol):
    stock = yf.Ticker(symbol)
    try:
        # 에러 메시지를 무시하기 위해 stderr를 일시적으로 redirect
        with contextlib.redirect_stderr(io.StringIO()):
            info = stock.info
        # info가 비어있으면 유효하지 않은 심볼로 간주
        if info and 'symbol' in info:
            return True  # 유효한 symbol
    except Exception:
        pass  # 에러가 발생해도 아무것도 출력되지 않음
    return False  # 유효하지 않은 symbol

# 테스트
symbols = ["AAPL", "INVALIDSYM", "MSFT"]
for symbol in symbols:
    if check_symbol(symbol):
        print(f"{symbol} is valid.")
    else:
        print(f"{symbol} is invalid.")

```

### 3. 판다스 관련
\- to_excel()시 index=True, index_label="No" : 이거 안 해주면 Unnamed 컬럼 생기면서 새로 적재하기 힘들어짐  

### 4. OOP 연습 필요

# 4. 에러 목록

## 4-1. 순번 / 에러명 / 원인 / 해결  

\- 1. / client 404에러 / yfinance stock.info 조회 시 안 뜨는 티커들 존재 / stock.info 전에 try except 예외처리. 사실, 그냥 add_stock_info 함수 내에서 반복문 시작하자마자 예외처리 조졌으면 다 잘 해결됐을 거임  
\- 2. / json.decoder.JSONDecodeError / 1번과 같음 / 1번과 같음  
\- 3. / AttributeError: 'float' object has no attribute 'upper' / stock_data = yf.Ticker(symbol) 부분에서 뜨는 오류. Symbol중에서 float인 게 하나도 없는데 왜 뜨는지는 모르겠음 / stock_data = yf.Ticker(symbol) 전에 try except 예외처리  
\- 4. / Thread Exception / 2번이나 다른 이유로 쓰레드 작업 비정상 종료 시 발생 / 예외처리 적절하게 해줘서 1, 2 등 오류 안 뜨면 해결  
\- 5. / ValueError: No objects to concatenate / Thread들이 비정상 종료되어 합칠 데이터프레임들이 하나도 없어서 발생 / 1개 쓰레드라도 작업 완료하면 안 뜸. 3을 해결하면 되고, 이를 위해 1, 2번 해결 필요  
\- 6. / 완성된 엑셀에 일부 종목들 누락 / Thread간 속도 차이? 일부 쓰레드 작업 완료 안 됐는데 프로그램 종료 / 불완전 해결. 1~4번 에러들을 해결하려다보니 241119 성공. 아마 1번 에러가 지대한 영향을 끼친 게 아닐까? try except 예외처리 위치로 해결했다고 봐야할듯  
