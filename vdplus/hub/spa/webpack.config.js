const path = require("path");
const webpack = require("webpack");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer")
  .BundleAnalyzerPlugin;
const autoprefixer = require("autoprefixer");

const is_prod = process.env.VD_ENV === "production";

if (is_prod) {
  mode = "production";
} else {
  if (process.env.VD_ENV === "test") {
    mode = "test";
  } else {
    mode = "development";
  }
}

if (mode == "test" || mode == "development") {
  API_SERVER = "localhost:8000";
} else {
  API_SERVER = "/";
}

const isDevServer = process.env.WEBPACK_DEV_SERVER;

module.exports = {
  mode: mode,
  optimization: {
    providedExports: true,
    usedExports: true
  },
  devtool: is_prod ? false : "#sourcemap",
  devServer: {
    historyApiFallback: true,
    overlay: true,
    hot: true,
    proxy: {
      "/api/*": {
        target: "http://" + API_SERVER,
        secure: false,
        changeOrigin: true
      }
    }
  },
  entry: "./src/main.ts",
  output: {
    publicPath: isDevServer ? "/" : "/assets/",
    path: __dirname + "/dist",
    filename: "bundle.js"
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "VisiData",
      template: "index.html"
    }),
    new MiniCssExtractPlugin({
      // Options similar to the same options in webpackOptions.output
      // both options are optional
      filename: is_prod ? "[name].[hash].css" : "[name].css",
      chunkFilename: is_prod ? "[id].[hash].css" : "[id].css"
    }),
    new webpack.DefinePlugin({
      "ENV.mode": JSON.stringify(mode),
      "ENV.API_SERVER": JSON.stringify(API_SERVER)
    }),
    new CopyWebpackPlugin([{ from: "robots.txt" }, { from: "favicon.ico" }])
  ],
  module: {
    rules: [
      {
        test: /\.(js|jsx|tsx|ts)$/,
        exclude: /node_modules/,
        loader: "babel-loader"
      },
      {
        test: /\.(gif|png|jpe?g|svg)$/i,
        use: [
          "file-loader",
          {
            loader: "image-webpack-loader",
            options: {
              disable: true // webpack@2.x and newer
            }
          }
        ]
      },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              // you can specify a publicPath here
              // by default it uses publicPath in webpackOptions.output
              publicPath: "../",
              hmr: mode === "development"
            }
          },
          {
            loader: "css-loader"
          },
          {
            loader: "postcss-loader",
            options: {
              plugins: () => [autoprefixer()]
            }
          },
          {
            loader: "sass-loader",
            options: {
              sourceMap: is_prod,
              prependData: '@import "src/assets/base_theme";',
              sassOptions: {
                includePaths: [path.join(__dirname, "node_modules")]
              }
            }
          }
        ]
      }
    ]
  },
  resolve: {
    modules: [path.resolve(__dirname, "src"), "node_modules"],
    extensions: [".ts", ".tsx", ".js", ".jsx", ".scss"]
  }
};

if (process.env.DEPS_ANALYZE === "true") {
  module.exports.plugins.push(new BundleAnalyzerPlugin());
}
