import requests # 네이버 통신 라이브러리

# ==========================================
# 1. 네이버 지도 API 인증 정보 및 변환 함수
# ==========================================

NAVER_CLIENT_ID = 'u5lebm1eub'
NAVER_CLIENT_SECRET = 'SQ6lnnL5E9dbrzsoc2pWAqrcJAnifEgPcI2sSyTt' # [impo] 배포전에 .env 비밀 환경변수 파일에 따로 저장하기

# 장소를 입력받아 (위도, 경도)를 반환하는 함수
def get_lat_lng(location : str):
    url = 'https://maps.apigw.ntruss.com/map-geocode/v2/geocode'
    headers = {
        'x-ncp-apigw-api-key-id' : NAVER_CLIENT_ID,
        'x-ncp-apigw-api-key' : NAVER_CLIENT_SECRET,
        'Accept': 'application/json' # 공식 문서에 명시된 응답 데이터 형식 헤더 추가
    }
    params = {'query' : location}

    try :
        response = requests.get(url, headers = headers, params = params)

        # API 응답 상태 코드가 200(성공)이 아니면 에러 출력
        if response.status_code != 200:
            print('네이버 API 호출 실패 CODE :', response.status_code, response.text)
            return None, None

        data = response.json()

        # 네이버에서 검색 결과(주소)를 찾고 좌표를 뽑는 과정
        if data.get('addresses') and len(data['addresses']) > 0:
            lon = float(data['addresses'][0]['x']) # x는 경도
            lat = float(data['addresses'][0]['y']) # y는 위도
            return lat, lon
        else:
            # 주소 검색 결과가 0건일 때 터미널에 안내 출력
            print(f"'{location}'에 대한 주소 검색 결과가 없습니다. (도로명 주소로 입력해주세요)")
        
    except Exception as e:
        print('지도 API 에러 발생 :', e)

    # 검색 결과가 없거나 에러가 나면 None
    return None, None