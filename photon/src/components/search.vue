<template>
  <div>
    <!-- <link rel="stylesheet" href="./css/index.css"> -->
    <div class="imgbox">
        <!-- <img src="./images/2022.png" alt=""> -->
    </div>
    <div id="data">
        <select name="" id="">
        <!-- 我将各个平台的域名和搜索关键字都放在了下拉框的value中，
        方便后面js获取，另外一定给某一平台添加默认选中状态 -->
        <option value="https://www.baidu.com/s" selected>百度</option>
        <option value="https://cn.bing.com/search">BING</option>
        <option value="https://yandex.com/search/">Yandex</option>
        <option value="https://juejin.cn/search">掘金</option>
        <option value="https://zzk.cnblogs.com/s">博客园</option>
        <option value="https://www.jianshu.com/search">简书</option>
        <option value="https://so.csdn.net/so/search">CSDN</option>
        <option value="https://www.51yuansu.com/index.php">觅元素</option>
        <option value="https://www.aigei.com/s">爱给网素材</option>
        <option value="https://search.bilibili.com/all">B站</option>
        <option value="https://www.haiantv.cc/word">影视一键搜</option>
    </select>
        <input type="text" name="" id="text">
        <button class="label" type="button">搜索</button>
    </div>
  </div>
</template>

<script setup lang="ts">

</script>
<style scoped lang="scss">
</style>
