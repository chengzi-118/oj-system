import streamlit as st
import requests
import json
import time
import pandas as pd

st.set_page_config(
    page_title="在线评测系统",
    layout="wide"
)

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

# 初始化会话状态
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'requests_session' not in st.session_state:
    st.session_state.requests_session = requests.Session()

def make_request(method, endpoint, data = None, params = None):
    """
    Use API to make requests.
    """
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    session = st.session_state.requests_session
    
    try:
        if method == "GET":
            response = session.get(url, params=params, headers=headers)
        elif method == "POST":
            response = session.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = session.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = session.delete(url, headers=headers)
        
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"code": 500, "msg": f"网络请求失败: {str(e)}", "data": None}, 500
    except json.JSONDecodeError:
        return {"code": 500, "msg": "响应格式错误", "data": None}, 500
    except Exception as e:
        return {"code": 500, "msg": f"未知错误: {str(e)}", "data": None}, 500

def show_response(response, status_code):
    """
    Dealing with reasponse.
    """
    if status_code == 200:
        st.success(response.get('msg', 'Success'))
    elif status_code == 400:
        st.error(f"参数错误: {response.get('msg', 'Bad Request')}")
    elif status_code == 401:
        st.error("请先登录")
        st.session_state.logged_in = False
        st.session_state.user_info = None
    elif status_code == 403:
        st.error(f"权限不足: {response.get('msg', 'Forbidden')}")
    elif status_code == 404:
        st.error(f"资源不存在: {response.get('msg', 'Not Found')}")
    elif status_code == 429:
        st.error(f"请求过于频繁: {response.get('msg', 'Too Many Requests')}")
    else:
        st.error(f"错误 {status_code}: {response.get('msg', 'Unknown error')}")

def login_page():
    st.title("用户登录")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("用户登录")
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            login_submitted = st.form_submit_button("登录", use_container_width=True)
            
            if login_submitted:
                if not username or not password:
                    st.error("请填写用户名和密码")
                else:
                    with st.spinner("正在登录..."):
                        response, status_code = make_request("POST", "/auth/login", {
                            "username": username,
                            "password": password
                        })
                        
                        if status_code == 200:
                            st.session_state.logged_in = True
                            st.session_state.user_info = response['data']
                            st.success("登录成功！")
                            time.sleep(1)
                            st.rerun()
                        else:
                            if status_code == 401:
                                st.error("用户名或密码错误，请重试")
                            elif status_code == 403:
                                st.error("账户已被禁用，请联系管理员")
                            else:
                                show_response(response, status_code)
    
    with col2:
        st.subheader("用户注册")
        with st.form("register_form"):
            reg_username = st.text_input("用户名", placeholder="请输入用户名")
            reg_password = st.text_input(
                "密码",
                type="password",
                placeholder="请输入密码"
            )
            register_submitted = st.form_submit_button("注册", use_container_width=True)
            
            if register_submitted:
                if not reg_username or not reg_password:
                    st.error("请填写用户名和密码")
                else:
                    with st.spinner("正在注册..."):
                        response, status_code = make_request("POST", "/users/", {
                            "username": reg_username,
                            "password": reg_password
                        })
                        
                        if status_code == 200:
                            st.success("注册成功！请登录")
                        else:
                            show_response(response, status_code)

def submission_page():
    st.title("代码提交与查询")

    if 'last_submission_id' not in st.session_state:
        st.session_state.last_submission_id = ""
    if 'polling_active' not in st.session_state:
        st.session_state.polling_active = False

    st.subheader("提交代码")

    with st.form("submit_form"):
        col1, col2 = st.columns([1, 1])

        with col1:
            problem_id = st.text_input(
                "题目ID",
                placeholder="请输入题目ID",
                key="problem_id_input"
            )
            language = st.selectbox("编程语言", ["python", "cpp"], key="language_select")

        with col2:
            st.write("")

        code = st.text_area(
            "代码",
            height=400,
            placeholder="请在此输入您的代码...",
            key="code_input"
        )

        submit_button = st.form_submit_button("提交评测", use_container_width=True)

        if submit_button:
            if not problem_id or not language or not code:
                st.error("请填写所有必填字段")
            else:
                with st.spinner("正在提交..."):
                    response, status_code = make_request("POST", "/submissions/", {
                        "problem_id": problem_id,
                        "language": language,
                        "code": code
                    })

                    if status_code == 200:
                        submission_id = response['data']['submission_id']
                        st.success(f"提交成功！评测ID: {submission_id}")
                        st.session_state.last_submission_id = submission_id
                        st.session_state.polling_active = True
                    else:
                        show_response(response, status_code)

    st.markdown("---")

    st.subheader("查询评测结果")

    if st.session_state.last_submission_id:
        st.info(f"最近提交ID: {st.session_state.last_submission_id}")

    submission_id_query = st.text_input(
        "评测ID",
        value=st.session_state.last_submission_id,
        placeholder="请输入评测ID",
        key="submission_id_query_input"
    )

    col_query_buttons = st.columns([1, 1, 1])

    with col_query_buttons[0]:
        if st.button("查询结果", use_container_width=True, key="query_result_button"):
            if not submission_id_query:
                st.error("请输入评测ID")
            else:
                with st.spinner("正在查询..."):
                    response, status_code = make_request(
                        "GET", f"/submissions/{submission_id_query}"
                    )

                    if status_code == 200:
                        result = response['data']
                        st.success("查询成功！")
                        col_score, col_total = st.columns(2)
                        with col_score:
                            st.metric("得分", result.get('score', 0))
                        with col_total:
                            st.metric("总分", result.get('counts', 0))
                    else:
                        show_response(response, status_code)

    with col_query_buttons[1]:
        if st.button("查询详细日志", use_container_width=True, key="query_log_button"):
            if not submission_id_query:
                st.error("请输入评测ID")
            else:
                with st.spinner("正在查询详细日志..."):
                    response, status_code = make_request(
                        "GET", f"/submissions/{submission_id_query}/log"
                    )

                    if status_code == 200:
                        log_data = response['data']
                        st.success("查询成功！")
                        st.metric(
                            "总得分",
                            f"{log_data.get('score', 0)}/{log_data.get('counts', 0)}"
                        )

                        if 'details' in log_data and log_data['details']:
                            st.subheader("测试点详情")
                            df = pd.DataFrame(log_data['details'])

                            def color_result(val):
                                if val == 'AC':
                                    return 'background-color: lightgreen'
                                elif val == 'WA':
                                    return 'background-color: red'
                                elif val == 'TLE':
                                    return 'background-color: lightyellow'
                                elif val == 'MLE':
                                    return 'background-color: brown'
                                else:
                                    return 'background-color: lightpink'
                            styled_df = df.style.applymap(
                                color_result,
                                subset=['result']
                            )
                            st.dataframe(styled_df, use_container_width=True)
                        else:
                            st.info("详细日志不可见或暂无数据")
                    else:
                        show_response(response, status_code)

    with col_query_buttons[2]:
        if st.button(
            "自动轮询",
            use_container_width=True,
            key="auto_poll_button"
        ) or st.session_state.polling_active:
            if not submission_id_query:
                st.error("请输入评测ID")
                st.session_state.polling_active = False
            else:
                st.info("开始轮询评测结果...")
                placeholder = st.empty()

                for i in range(20):
                    with placeholder.container():
                        with st.spinner(f"第{i+1}次查询中..."):
                            response, status_code = make_request(
                                "GET", f"/submissions/{submission_id_query}"
                            )

                            if status_code == 200:
                                result = response['data']
                                if 'score' in result and 'counts' in result:
                                    st.success("评测完成！")
                                    col_score, col_total = st.columns(2)
                                    with col_score:
                                        st.metric("得分", result['score'])
                                    with col_total:
                                        st.metric("总分", result['counts'])
                                    st.session_state.polling_active = False
                                    break
                                else:
                                    st.info(f"评测中... 当前状态: {result.get('status')}")
                            else:
                                st.error("查询失败")
                                show_response(response, status_code)
                                st.session_state.polling_active = False
                                break

                    time.sleep(0.1)
                else:
                    st.warning("轮询超时，请手动查询或稍后重试。")
                st.session_state.polling_active = False

def main_page():
    st.title("在线评测系统")
    
    if st.session_state.user_info:
        st.sidebar.success(f"欢迎，{st.session_state.user_info.get('username', '用户')}！")
        st.sidebar.write(f"角色: {st.session_state.user_info.get('role', 'user')}")
        
        if st.sidebar.button("登出"):
            with st.spinner("正在登出..."):
                response, status_code = make_request("POST", "/auth/logout")
                
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.session_state.requests_session = requests.Session()
                
                if status_code == 200:
                    st.success("已登出")
                else:
                    st.info("已清除本地登录状态")
                
                time.sleep(1)
                st.rerun()
    
    st.subheader("题目列表")
    
    if st.button("刷新题目列表"):
        with st.spinner("正在获取题目列表..."):
            response, status_code = make_request("GET", "/problems/")
            
            if status_code == 200:
                problems = response['data']
                if problems:
                    df = pd.DataFrame(problems)
                    st.dataframe(df, use_container_width = True)
                else:
                    st.info("暂无题目")
            else:
                show_response(response, status_code)
    
    st.subheader("开始编程")
    if st.button("前往代码提交", use_container_width = True):
        st.session_state.page = "submission"
        st.rerun()

def main():
    if 'page' not in st.session_state:
        st.session_state.page = "main"
    
    if st.session_state.logged_in:
        st.sidebar.title("导航")
        if st.sidebar.button("主页"):
            st.session_state.page = "main"
            st.rerun()
        if st.sidebar.button("代码提交"):
            st.session_state.page = "submission"
            st.rerun()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.page == "main":
            main_page()
        elif st.session_state.page == "submission":
            submission_page()

if __name__ == "__main__":
    main()