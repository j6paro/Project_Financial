"""
* 이력
241110일
1. 각 스레드 작업 끝날 때마다 엑셀 파일 호출이 아닌, 데이터 프레임 리스트에 저장 후 나중에 한꺼번에 concat
-> 갑자기 든 생각인데... openpyxl 꼭 써야함? 그냥 데이터프레임만 써도 되는 거 아녀?
-> 엑셀에 데이터 업데이트 안되는 것 개선 완료
2. 모든 스레드들 작업 끝난 뒤에 프로그램 끝내기 위해 while문 안에 멀티 쓰레딩 넣음
-> 그러니까 cnt_process가 4 될 때까지 전체 멀티 쓰레딩을 반복함. add_stock_info() 함수 마지막에만 while문을 넣자. 이러면 그냥 아예 멈춰버림.. 음... 
-> time.sleep(30)을 깔아보자. 이것도 실패.
-> 2번 대문처럼 while문 안에 멀티 쓰레딩 넣고, 완료된 애들은 ranges에서 삭제하자. 그리고 다 될 때까지 쓰레딩 돌리자.
3. 스레드 개수에 따른 성능(num_cpu 수) : 241110일, 스레드 개수는 4개가 최적인듯
- 6 : 약 26분
- 4 : 약 22분
- 3 : 약 54분

241115금
4. 뭔가... deepcopy하면서 쓰레드 부분 좋버그 걸린 것 같구요
-> 아니면 add_stock_info함수에서 df_stocks_for_thread를 global로 부르면서 좋버그? 스레드로 작업 끝난 df를 add_stock_info()가 아닌 multi_thread()에서 삭제하자
5. json.decoder.JSONDecodeError 뜨면서 갑자기 잘 진행되던 애들 사라짐. 음... 사라진 종목들이 있는건가?
6. 404 clienterror 왜 뜨는지 알아냄. 이상한 종목들 껴있는데, 해당 종목들에 대해 .info 할 때마다 뜨는거임

241117일
7. 모든 쓰레드들 일단 쓰레드 리스트에 넣고, 반복문으로 start함
8. 아니 무슨 결과물도 못 만들어내길래 일단 다시 client error도 뜨게하는 걸로 바꿈. 뭐가 문제냐...
9. except JSONDecodeError 예외처리를 try: stock.info로 처음에 해줬어야 하는 듯. 지표들 가져오기 전에
-> 예외처리 제대로 안 제껴진 것 같다고 느낀 이유가 이거인 듯

241118월
10. 오케이, 일단 정상 실행 완료. 실행시간 45:04

* 해야할 것들
1. 404 client error도 예외처리
-> stderr 관련 해서 처리하면 돼
2. stderr 관련, 에러 뜨면 그냥 넘겨버리는 걸로. 나는 이렇게 에러메세지가 뜨면 시간이 단축될줄 알고 했던건데...

* 배운 것들 +
1. 241110일. read_excel, to_excel에서 인덱스 설정 안해주면 Unnamed? 생기면서 컬럼이 추가됨. 그래서 다른 날 다시 코드 돌리면 지표들이 추가가 제대로 안됨. 왜냐하면 이상한 컬럼들 양식들로 변질됐거든
2. 241115금. except 예외처리 여러 개 하는 법 : 튜플, Exception 하면 모든 에러에 대해 예외처리
3. get()
4. 챗GPT가 테스트 코드? 잘 짜주네
5. contextlib, io
6. 241118월. 아무리 긴 에러도, 패키지에서 일어난 에러도, 잘 보면 어떤 패키지에서 문제가 생겼는지, 패키지의 어떤 함수, 코드가 문제를 일으켰는지 알 수 있다.
7. + 컴퓨터에서 라이브러리 위치 찾는 법
- https://nadocoding.tistory.com/81

* 에러 정리
1. 404 client Error : 좀 영세한 기업의 경우 조회가 안 되는 듯?
2. JSONDecodeError : 1번과 마찬가지 이유

* 방향
1. 이전 제한된 종목(미국 한정)에 멀티쓰레딩
2. 전종목, 멀티 쓰레딩 사용 안함
"""

import yfinance as yf
from tqdm import tqdm
import pandas as pd
import numpy as np
from datetime import datetime
import time
import threading
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

### 변수들 모음

# 상수(파일 저장 경로 같은) 등 모음
URL_NYSE = "https://www.nyse.com/listings_directory/stock"  # NYSE 주소
DIR_NYSE_STOCK_LIST = "C:/coding/DA/재테크/미국기업목록/nyse_stocks.xlsx"  # NYSE에서 긁어온 전종목 저장하는 곳
DIR_STOCK_INDICATOR = "C:/coding/DA/재테크/stocks_basic_indicators.xlsx"  # 작업 후 다 만들어진 파일 저장할 경로
lock = threading.Lock()  # 락
start_time = time.time()  # 시작 시간
num_cpu = os.cpu_count()  # 일 나눠서할 cpu 개수
cnt_nyse = os.path.isfile(
    DIR_NYSE_STOCK_LIST
)  # NYSE에서 나스닥 상장 전종목을 파일이 있는가?

# 날짜 관련
now = datetime.now()  # 오늘 날짜 가져오기
today = str(now).split()[0]  # 긴 형식의 날짜 ex) 2024-10-27 (2024년 10월 27일)

# User-Agent 설정
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"  # User-Agent 설정. 스팸봇으로 오해하지 않도록
header = {"User-Agent": user_agent}  # 요청 헤더 설정

# 스레드로 데이터프레임 따로 작업한 후 concat할 데이터프레임 모아놓는 리스트들
list_dfs = list()
cnt = 0  # 모든 쓰레드들 작업 끝냈는지 확인할 카운터
df_for_delete = (
    list()
)  # 쓰레드에서 작업 끝낸 애들 추가. multi_thread() 함수에서 삭제할거야!


### 함수들 모음
# NYSE에서 나스닥 상장 전종목 스크랩
def scrap_nyse():
    cnt_page = 1  # 현재 몇 페이지 스크래핑 중인지 표시
    chromedriver_autoinstaller.install()  # 크롬 드라이버 최신버전으로 업데이트
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--headless")  # 백그라운드 모드 추가

    # 웹드라이버 시작
    driver = webdriver.Chrome(options=options)
    driver.get(URL_NYSE)

    # 빈 데이터프레임 생성
    columns = ["Symbol", "Name"]
    df_nyse = pd.DataFrame(columns=columns)

    print("나스닥 상장 종목 수집 중")
    try:  # 페이지 넘기면서 기업 정보 수집
        while True:  # 테이블 로드 대기
            if cnt_page % 50 == 0:
                print(f"현재 수집 중인 페이지 : {cnt_page}")
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[1]/table/tbody',
                    )
                )
            )  # 테이블 정보 가져오기
            rows = driver.find_elements(
                By.XPATH,
                '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[1]/table/tbody/tr',
            )  # 첫 번째 줄
            for row in rows:  # 각 행에서 심볼과 기업명 추출
                symbol = row.find_element(By.XPATH, "./td[1]").text
                name = row.find_element(By.XPATH, "./td[2]").text
                df_concat = pd.DataFrame([{"Symbol": symbol, "Name": name}])
                df_nyse = pd.concat([df_nyse, df_concat], ignore_index=True)

            # 다음 버튼 클릭 대기 및 클릭
            next_btn = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        '//*[@id="integration-id-fcc63aa"]/div[1]/div[3]/div[2]/div[2]/div[2]/div/ul/li[8]/a/span',
                    )
                )
            )
            next_btn.click()
            cnt_page += 1

    except Exception as e:
        print(f"에러 발생: {e}")

    finally:  # 크롤링 종료 후 데이터 저장
        driver.quit()
        df_nyse.to_excel(DIR_NYSE_STOCK_LIST, index=True, index_label="No")
        print("나스닥 종목 저장 완료: nyse_stocks.xlsx")


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
            print(f"에러 심볼 : {symbol}, 에러명 : {e}")
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

    lock.acquire()
    list_dfs.append(data_reset.reset_index(drop=True))
    cnt += 1  # 1개 쓰레드 작업 완료하면 cnt +1
    df_for_delete.append(data)  # 완료된 데이터프레임은 삭제할 데이터프레임에도 추가
    lock.release()
    print("스레드 끝", cnt)  # 디버깅용


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
    df_stocks_nyse = pd.read_excel(
        DIR_NYSE_STOCK_LIST, index_col=0
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
    global cnt
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

    if (
        cnt != 0
    ):  # 작업 끝낸 쓰레드가 생겨난다면, df_for_delete에 삭제할 df들 추가됐겠지? 삭제 드가자
        for df in df_for_delete:
            df_stocks_for_thread.remove(df)


if __name__ == "__main__":
    if (not cnt_nyse) or (
        now.month % 2 == 0
    ):  # 나스닥 전 종목 파일이 없거나, 짝수 달이라면 NYSE 전 종목 파일 업데이트
        scrap_nyse()

    multi_thread()  # 멀티 쓰레딩

    save_df()  # 데이터프레임 엑셀로 저장

    check_time()  # 실행시간 출력
