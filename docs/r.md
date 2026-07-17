## 阿里万象 文字生成视频请求
```sh
curl --location 'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis' \
--header 'X-DashScope-Async: enable' \
--header 'Content-Type: application/json' \
--header 'Authorization: ••••••' \
--data '{
    "model": "wan2.7-t2v",
    "input": {
        "prompt": "客厅正中央，一只穿纸尿裤的小橘猫正威风凛凛地骑在一匹光溜溜没有尾巴的玩具木马上，头顶歪扣着半个柚子皮做的头盔，皮带扣刚好卡住肉嘟嘟的下巴，嘴里死死叼着安抚奶嘴，右爪高高举起鸡毛掸子当作长枪，面前的地板上摆开了一堆积木搭的“城堡”、几只毛绒兔子、一排小兵人和一辆红色玩具卡车，被他视作必须攻破的“楼兰大军”，远处沙发像雪山，电视柜像孤城，夕阳斜照进来给这只小毛球镀上一层金光，只见他深吸一口气（奶嘴差点滑落），用尽全身奶劲念出自己改编的出征诗：“客厅地垫铺黄沙，玩具兵团排阵牙，柚子盔歪奶嘴紧，不掀积木不归家！”——话音刚落，他便挥动掸子猛地戳向积木塔，哗啦一声“城堡”倒塌，小橘猫满意地打了个喷嚏，纸尿裤上沾满了柚子皮的清香，而那只没有尾巴的木马还在原地晃晃悠悠，仿佛也在为这场奶香四溢的“客厅萌朝大战”无声助威。"
    },
    "parameters": {
        "resolution": "720P",
        "ratio": "9:16",
        "prompt_extend": true,
        "watermark": false,
        "duration": 15
    }
}'
```

## 查询任务结果

```sh
curl --location 'https://dashscope.aliyuncs.com/api/v1/tasks/ba20a885-3f66-4e76-a8d6-223477d3919c' \
--header 'Authorization: *******'
```
