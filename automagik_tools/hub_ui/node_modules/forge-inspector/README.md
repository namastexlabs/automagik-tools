# Forge Inspector

This package adds point-and-click edit functionality to web apps, when used with [Automagik Forge](https://automagikforge.com).

Works with frameworks like [Next.js](https://nextjs.org/),
  [Create React App](https://create-react-app.dev/),
  & [Vite](https://github.com/vitejs/vite/tree/main/packages/plugin-react)
  that use [@babel/plugin-transform-react-jsx-source](https://github.com/babel/babel/tree/master/packages/babel-plugin-transform-react-jsx-source)

## Installation

Even though `forge-inspector` is added to `dependencies`, [tree-shaking](https://esbuild.github.io/api/#tree-shaking) will remove `forge-inspector` from `production` builds.

Add this dependency to your project:
```shell
npm i forge-inspector
```

## Usage

<details>
<summary>Create React App</summary>

```diff
+import { ForgeInspector } from 'forge-inspector';
 import React from 'react';
 import ReactDOM from 'react-dom/client';
 import './index.css';
@@ -8,7 +7,6 @@ import reportWebVitals from './reportWebVitals';
 const root = ReactDOM.createRoot(document.getElementById('root'));
 root.render(
   <React.StrictMode>
+    <ForgeInspector />
     <App />
   </React.StrictMode>
 );
```

</details>

<details>
<summary>Next.js</summary>

```diff
+import { ForgeInspector } from 'forge-inspector'
 import type { AppProps } from 'next/app'
 import '../styles/globals.css'

 function MyApp({ Component, pageProps }: AppProps) {
   return (
     <>
+      <ForgeInspector />
       <Component {...pageProps} />
     </>
   )
```

</details>

<details>
<summary>Vite</summary>

```diff
+import { ForgeInspector } from "forge-inspector";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
+   <ForgeInspector />
  </React.StrictMode>
);
```

</details>

## Credits

Thanks to [Eric Clemmons](https://github.com/ericclemmons) for creating the original [Click-To-Component](https://github.com/ericclemmons/click-to-component) library, from which our helper is forked from.