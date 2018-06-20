var tesseract = require('node-tesseract')

// Recognize text of any language in any format

const t = new Date().getTime()
tesseract.process('./score.png', function (err, text) {
  if (err) {
    console.error(err)
  } else {
    console.log(text)
  }
  console.log(new Date().getTime() - t)
})
