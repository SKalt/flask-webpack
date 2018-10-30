const path = require('path')
module.exports = {
  context: path.resolve(__dirname, 'src/'),
  entry: {
    'foo': './foo.js',
    'bar': './bar.js',
  },
  output: {
    filename: '[name].[chunkhash].js',
  }
}
