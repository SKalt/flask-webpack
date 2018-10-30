
module.exports = require('webpack-merge')(
  require('./webpack.config.js'),
  {
    entry: {
      index: './index-async.js'
    },
  }
);
