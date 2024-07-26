SendMessage(
                    original_content_url=chart_link,
                    preview_image_url=pre_chart_link)
                line_bot_api.reply_message(event.reply_token, image_message)
        elif check == 'ai:' and get_request_user_id in auth_user_ai_list:
            try:
                client = OpenAI(api_key=openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "如果回答問題盡可能用簡潔的話回復"
                        },
                        {
                            "role": "user",
                            "content": user_msg,
                        },
                    ],
                )
                reply_msg = response.choices[0].message.content
                print('reply_msg', reply_msg)
                message = TextSendMessage(text=reply_msg)
                line_bot_api.reply_message(event.reply_token, message)
            except Exception as e:
                print(e)
        else:  # 學使用者說話

            message = TextSendMessage(text=event.message.text)
            line_bot_api.reply_message(event.reply_token, message)
    else:
        message = TextSendMessage(text='使用者沒有權限')
        line_bot_api.reply_message(event.reply_token, message)


if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5001))
    # local
    # app.run(host='0.0.0.0', port=5001)
    # Render
    app.run()





