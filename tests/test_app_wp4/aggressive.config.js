const merge = require('webpack-merge')
module.exports = merge(
  require('./webpack.config.js'),
  {
    entry: {
      index: './index-split.js'
    },
    optimization: {
      splitChunks: {
        cacheGroups: {
          commons: {
            name: 'commons',
            chunks: 'initial',
            minChunks: 2
          }
        }
      }
    },
  }
)
