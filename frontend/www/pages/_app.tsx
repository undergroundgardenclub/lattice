import React from "react";
// https://github.com/styled-components/styled-components/issues/1593
import "../components/global.css";

export default ({ Component, pageProps }) => {
  return <Component {...pageProps} />;
};
