# Project_Financial
The topic of this projects is financial. It's about financial indicators scrapping, using cloud etc.

# 1. 개요

## 1-1. 설명
\- 미국 주식 종목 선정시 참고할 수 있는 기본 지표들을 스크래핑 하는 코드를 작성한다.  
\- 1차 목표는 수동으로 실행시키는 코드의 완성, 2차 목표는 클라우드를 활용해 배치 프로세스로 일정 주기마다 자동으로 종목의 지표들을 받아올 수 있도록 한다.

# 2. 코드

## 2-1. 전체적인 흐름

\- (1) NYSE에서 나스닥에 상장된 전 종목 리스트 스크랩 -> (2) 각 종목에 대해 야후 파이낸스에서 PER, PBR 등 투자 기본 지표들 받아오기 -> (3) 각 지표들에 기준을 두고 저PER, 저PBR 종목 등 선별하기  
\- 각 단계에서 사용된 주요 패키지, 라이브러리는 다음과 같다.  
\- (1) : selenium  
\- (2) : yfinance  
\- (3) : pandas, openpyxl  

```
# 전 종목 스크래핑으로
import yfinance as yf
from tqdm import tqdm
import pandas as pd
import numpy as np
from datetime import datetime
import time
from openpyxl import Workbook
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import threading
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# 상수 등 모음
URL_NYSE = "https://www.nyse.com/listings_directory/stock"  # NYSE 주소
DIR_NYSE_STOCK_LIST = "C:/coding/DA/재테크/미국기업목록/nyse_stocks.csv"  # NYSE에서 긁어온 전종목 저장하는 곳
DIR_STOCK_INDICATOR = "C:/coding/DA/재테크/stocks_basic_indicators.xlsx"  # 작업 후 다 만들어진 파일 저장할 경로
lock = threading.Lock()  # 락


### 함수 영역 ###
# 각 주식 지표 데이터 가져오기
def add_stock_info(data):
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
            ):  # 영업이익 대폭 증가 주식 판별. 영업이익 5% 상승 기준
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

    lock.acquire()  # 락 잠금
    data_reset = data_reset.reset_index(drop=True)
    make_or_edit_excel(data_reset)
    lock.release()  # 락 해제


# 엑셀파일 편집, 새로 생성 또는 수정 및 저장. stock_wb 는 stock_workbook 이라는 의미
def edit_excel(dataframe, file_exist):
    stock_wb = load_workbook(DIR_STOCK_INDICATOR, read_only=False, data_only=False)
    stock_ws = stock_wb.active
    # 보충 필요1 -> 만약 빈 엑셀이면 header=True
    # 보충 필요2 -> 만약 header=False면 빈 행 삭제하기
    for r in dataframe_to_rows(dataframe, index=True, header=file_exist):
        stock_ws.append(r)
    stock_wb.save(DIR_STOCK_INDICATOR)
    stock_wb.close()


# 기본지표 정리된 엑셀 없으면 새로 생성, 있으면 편집
def make_or_edit_excel(dataframe):
    is_file = False
    if os.path.isfile(DIR_STOCK_INDICATOR):
        edit_excel(dataframe, is_file)
    else:
        is_file = True
        stock_wb = Workbook()
        stock_ws = stock_wb.active
        stock_wb.save(DIR_STOCK_INDICATOR)
        stock_wb.close()
        edit_excel(dataframe, is_file)


# 데이터프레임에서 비어있는 행 삭제하고 다시 엑셀로 저장
def delete_empty_rows():
    dataframe_delete_emptycell = pd.read_excel(DIR_STOCK_INDICATOR)
    dataframe_delete_emptycell = dataframe_delete_emptycell.replace("", pd.NA)
    dataframe_delete_emptycell = dataframe_delete_emptycell.dropna()
    dataframe_delete_emptycell.to_excel(DIR_STOCK_INDICATOR)


### 클래스 영역 ###
class Nasdaq_Indicators:
    def __init__(self):
        self.now = datetime.now()  # 오늘 날짜 가져오기
        self.today = str(self.now).split()[0]  # 오늘 날짜를 2024-11-05 이런 식으로
        self.df_stocks_nyse = pd.read_csv(
            DIR_NYSE_STOCK_LIST
        )  # 생성된 나스닥 파일 읽어서 DataFrame에 저장하고 빈 컬럼들 생성
        self.cnt_nyse = os.path.isfile(DIR_NYSE_STOCK_LIST)
        self.df_stocks_nyse = self.df_stocks_nyse.assign(
            DATE=self.today,
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
        # 날짜, cpu 변수들
        self.num_cpu = 6  # os.cpu_count() # 일 나눠서할 cpu 개수. cpu 코어 개수 vs 수동으로 개수 선정
        self.start_time = time.time()  # 시작 시간
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # User-Agent 설정. 스팸봇으로 오해하지 않도록
        self.header = {"User-Agent": self.user_agent}  # 요청 헤더 설정
        # NYSE 스크래핑 관련 변수들
        self.options = None  # 뒤에 run_scrap 함수에서 크롬옵션 받아올거임
        self.driver = None  # 뒤에서 웹드라이버 시작하는 애가 될거임
        self.df_nyse = pd.DataFrame(
            columns=["Symbol", "Name"]
        )  # 전종목 긁어오기 위한 데이터프레임 생성
        self.cnt_page = 1  # NYSE에서 스크랩할 때 현재 몇 페이지 스크래핑 중인지 표시
        self.rows = None  # 뒤에서 NYSE 종목들 긁어와서 넣어줄 거야
        self.next_btn = None  # 다음 버튼 클릭하는 객체. 뒤에서 부여 예정
        # 멀티쓰레딩 관련 변수들
        self.ranges = np.array_split(np.array(self.df_stocks_nyse.index), self.num_cpu)
        self.result_dataframes = (
            []
        )  # 미국주식 목록 데이터프레임 쪼갠 뒤, add_stock_info 함수를 거친 데이터프레임들을 다시 합쳐주기 위해 한 리스트에 모을거임.
        self.thread_list = []  # 실행시킬 쓰레드들 목록
        self.df_stocks_for_thread = []  # 미국주식 목록 데이터프레임 쪼개서 담을 리스트

    def run_NYSE_scrap(self):  # NYSE에서 나스닥 상장 전 종목 리스트 받아오기
        chromedriver_autoinstaller.install()  # 크롬 드라이버 최신버전으로 업데이트
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.options.add_argument("--headless")  # 백그라운드 모드 추가
        self.options.add_argument(
            "--no-sandbox"
        )  # 리소스 제한이 있는 환경에서 사용할 때 유용
        self.options.add_argument("--disable-dev-shm-usage")  # 메모리 관련 오류 방지

        # 웹드라이버 시작
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.get(URL_NYSE)

        print("나스닥 상장 종목 수집 중")
        # 페이지 넘기면서 기업 정보 수집
        try:
            while True:
                # 테이블 로드 대기
                if self.cnt_page % 50 == 0:
                    print(f"현재 수집 중인 페이지 : {self.cnt_page}")
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[1]/table/tbody',
                        )
                    )
                )
                # 테이블 정보 가져오기
                self.rows = self.driver.find_elements(
                    By.XPATH,
                    '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[1]/table/tbody/tr',
                )  # 첫 번째 줄
                # 각 행에서 심볼과 기업명 추출
                for row in self.rows:
                    symbol = row.find_element(By.XPATH, "./td[1]").text
                    name = row.find_element(By.XPATH, "./td[2]").text
                    df_concat = pd.DataFrame([{"Symbol": symbol, "Name": name}])
                    self.df_nyse = pd.concat(
                        [self.df_nyse, df_concat], ignore_index=True
                    )

                # 다음 버튼 클릭 대기 및 클릭
                self.next_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[2]/div/ul/li[8]/a/span',
                        )
                    )
                )
                self.next_btn.click()
                self.cnt_page += 1

        except Exception as e:
            print(f"에러 발생: {e}")

        finally:  # 스크랩 종료 후 데이터 저장
            self.driver.quit()
            self.df_nyse.to_csv(DIR_NYSE_STOCK_LIST, index=False)
            print("나스닥 종목 저장 완료: nyse_stocks.csv")

    def multi_threading(self):  # 멀티쓰레딩으로 지표 스크랩
        for c in range(1, self.num_cpu + 1):
            globals()[f"df_stocks_split{c}"] = self.df_stocks_nyse.loc[
                self.ranges[c - 1][0] : self.ranges[c - 1][-1] + 1
            ]
            self.df_stocks_for_thread.append(eval(f"df_stocks_split{c}"))
        for d in self.df_stocks_for_thread:  # d는 dataframe
            t = threading.Thread(target=add_stock_info, args=(d,))
            t.start()
            self.thread_list.append(t)
        for t in self.thread_list:
            t.join()
        print("저장이 완료되었습니다.")  # yahoo finance 지표 가져오기 완료

    def check_time(self):
        runningtime = int(time.time() - self.start_time)
        runningtime_hour = runningtime // 3600  # 시간
        runningtime -= runningtime_hour * 3600
        runningtime_minute = runningtime // 60  # 분
        runningtime -= runningtime_minute * 60
        runningtime_second = runningtime  # 초
        print(f"실행시간 {runningtime_hour}:{runningtime_minute}:{runningtime_second}")

    def run_yf_scrap(self):  # yahoo finance에서 지표 스크랩하기
        if (not self.cnt_nyse) or (
            self.now.month % 2 == 0
        ):  # NYSE 종목 파일이 없거나, 짝수달인 경우 종목 업데이트
            self.run_NYSE_scrap()
        self.multi_threading()  # 멀티쓰레딩 실시
        delete_empty_rows()  # 엑셀 빈 행 제거
        self.check_time()  # 실행시간 표기


# 코드 실행
if __name__ == "__main__":
    scraper = Nasdaq_Indicators()
    scraper.run_yf_scrap()
```

# 3. 피드백

## 3-1. 추가, 수정할 것들

### 3-1-1. 241103_NYSE에서 나스닥 상장 전 종목 받아오기
\- 지금은 다음 종목들이 있는 페이지로 넘길 때 WebDriverWait(driver, 3) 이렇게 일정 시간 대기하라고 하고 있다. 하지만 [이 블로그](https://june98.tistory.com/11)에서는 일정 시간을 정한 게 아닌, 해당 요소가 화면에 표시될 때까지 대기하는 것도 가능하다.  
\-> 지금 다시 보니까 이미 내가 작성한 코드가 해당 기능을 적용한 것.

### 3-1-2. 241104_OOP 스타일로 코드 리팩토링
\- 지금은 변수, 함수들 너무 난잡하고 한 눈에 안 들어옴  
\-> 일단 OOP 스타일로 다시 정리하긴 했는데, 엄청 깔끔한 느낌은 들지 않는다. 매우 소소하게 깔끔해진 느낌? 무엇보다 챗gpt한테도 OOP 스타일로 리팩토링 해달라고 했는데 나보다 더 잘한 것 같음.  
\-> 310줄 -> 290줄로 줄이긴 함.

### 3-1-3. 241104_엑셀 생성하고 수정하는 함수의 사용 빈도, 존재 이유 생각
\- 속도에 방해되는 것 아닌가? 안정성도 떨어지는 것 같고. 그냥 데이터프레임 만들어서 파이썬 내부에서 여차저차 수정하는 게 낫지 않나? 데이터프레임 만들고 concat을 하는 게 낫지 않은가

## 3-2. 공부할 것들

### 3-2-1. 멀티쓰레딩, 멀티프로세싱 차이
\- 나는 멀티쓰레딩 사용했는데, 멀티프로세싱과 뭐가 다른지? 각각 언제 사용해야 하는지? 스레드와 프로세스는 뭔지?

### 3-2-2. 챗gpt OOP vs 내 OOP
\= 챗gpt가 나보다 코드 줄 수를 훨씬 많이 줄였음. 비교해보자.
