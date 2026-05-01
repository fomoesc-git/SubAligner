import { createApp } from "vue";
import { createPinia } from "pinia";
import { createRouter, createWebHashHistory } from "vue-router";
import App from "./App.vue";
import HomeView from "./views/HomeView.vue";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
  ],
});

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
