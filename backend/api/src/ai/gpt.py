import requests
import env

def gpt_completion_image_caption(image_base64, prompt="What's in this image?", max_tokens=300) -> str:
  headers = {
      "Content-Type": "application/json",
      "Authorization": f"Bearer {env.env_get_open_ai_api_key()}"
  }
  json = {
      "model": "gpt-4-vision-preview",
      "messages": [
          {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
          }
      ],
      "max_tokens": max_tokens
  }
  # request
  response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=json)
  # print(response.json())
  # request text
  response_text = response.json()["choices"][0]["message"]["content"]
  print(response_text)
  return response_text