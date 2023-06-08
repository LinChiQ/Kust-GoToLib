# Kust-GoToLib
适用于昆明理工大学的我去图书馆自动抢座程序


- 注意：该代码闲置时间较久，导致我自己都删除了源码，现在的源码并非是程序的源代码，已经封装好的程序可以正常使用，源代码**不保证能抢到，但releases里面的程序可以抢到**



使用方法：

- 本代码分有两个部分PickUp与ReserveTomorrow，即当日捡漏和明日预约

  ### **使用方法步骤**

  登录部分(使用[MikeWang000000/GoLibCookie: 我去图书馆 免抓包 获取Cookie (github.com)](https://github.com/MikeWang000000/GoLibCookie))

  1. 使用微信扫描下方二维码：    

  ![image.png](https://s2.loli.net/2023/06/04/BNFy6cLGozMIgwk.png)

  2. 点击微信右上角“…”符号，选择“复制链接”。

  ![image.png](https://s2.loli.net/2023/06/04/bmuDxYwf1cGjUnK.png)

  3. 将获得的 URL 链接，提交给 Python 脚本，即可获得 Cookie。

  ![image.png](https://s2.loli.net/2023/06/04/A9eRTDcmaFVIE4w.png)

- 在登录后根据不同的程序打开时不同的提示即可抢座，**尽量使用发布页面中的两个程序，源码暂时不保证能ok**

致谢：
- 登录部分使用[GoLibCookie](https://github.com/MikeWang000000/GoLibCookie)
- 明日预约的websocket使用[gotolibrary_websockets](https://github.com/xiaodouu/gotolibrary_websockets)
