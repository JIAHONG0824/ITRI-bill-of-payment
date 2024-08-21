import openai
import gradio as gr
import base64
import requests


def openai_api(prompt, key):
    openai.api_key = key
    completion = openai.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_image_content(base64_image, api_key):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "扮演影像識別專家，幫我把所有的細節都識別出來，包含學生姓名、就讀班級、學費金額、註冊金額、繳費總額。\
              另外，我很重視「印章內容」，包含印章中的日期",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # 如果發生HTTP錯誤，則會引發HTTPError異常
        image_content = response.json()["choices"][0]["message"]["content"]
        return image_content
    except Exception as err:
        print(f"Other error occurred: {err}")
        return get_image_content(base64_image)


def image_recognition(image, api_key):
    base64_image = encode_image(image)
    image_content = get_image_content(base64_image, api_key)
    prompt = (
        "扮演文字處理專家，幫我把逐字稿整理成格式：\
                原則1：若有註冊費，學費金額等於註冊費。若沒有註冊費，則學費金額為合計費用或總和費用或應繳金額或實繳金額。日期請注意力放在繳款日期或印章內的日期\
                原則2：輸出格式(但不用出現本句)：$student:| 學生姓名 $fee:| 學費金額 $date:| 繳款日期或印章上日期。$school:| 學校名稱。\
                原則3：Let's work this out in a step-by-step way to be sure we have the right answer.\
                原則4：以繁體中文來命題。逐字稿： "
        + image_content
    )
    result = openai_api(prompt, api_key)

    qname = result.split("$student:|")[1].split("$fee:|")[0].strip()
    qfee = result.split("$fee:|")[1].split("$date:|")[0].strip()
    qdate = result.split("$date:|")[1].split("$school:|")[0].strip()

    return qname, qfee, qdate


with gr.Blocks() as demo:
    gr.Markdown("繳費單查核")
    with gr.Tab("請依順序操作"):
        with gr.Row():
            file_input = gr.File(label="第一步：請上傳檔案")
            api_key_input = gr.Textbox(
                label="第二步：請輸入OpenAI API金鑰", placeholder="OpenAI API Key"
            )
            submit_button = gr.Button("第三步：開始識別")
        with gr.Row():
            qname = gr.Textbox(label="姓名", value="")
            qfee = gr.Textbox(label="金額", value="")
            qdate = gr.Textbox(label="日期", value="")

    submit_button.click(
        image_recognition,
        inputs=[file_input, api_key_input],
        outputs=[qname, qfee, qdate],
    )
