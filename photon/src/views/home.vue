<template>
  <div class="home">
    主页
    <search></search>
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import search from '../components/search.vue'

@Options({
  components: {
    search
  },
})
export default class home extends Vue {}
</script>