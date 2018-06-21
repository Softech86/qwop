const puppeteer = require('puppeteer-extra')
const Koa = require('koa')
const fs = require('fs')
const getPixels = require('get-pixels')
const tesseract = require('node-tesseract')
const sharp = require('sharp')

const config = JSON.parse(fs.readFileSync('config.json'))
puppeteer.use(require('puppeteer-extra-plugin-flash')())
const app = new Koa()
const Bus = {
  buffer: ''
}
const PEPPER = './PepperFlash'
const sleep = t => new Promise(resolve => setTimeout(resolve, t))
const pixels = buffer => new Promise((resolve, reject) => {
  getPixels(buffer, 'image/png', function (err, pixels) {
    if (err) {
      reject(err)
    } else {
      resolve(pixels)
    }
  })
})
const ocr = path => new Promise((resolve, reject) => {
  tesseract.process(path, function (err, text) {
    if (err) {
      reject(err)
    } else {
      resolve(text)
    }
  })
})

async function parseScreenshot (screenshot) {
  const ps = await pixels(screenshot)
  const center = ps.hi(164, 133).lo(148, 117).data // [148:164, 117:133]
  const centerCount = center.reduce((s, x) => s + x, 0) + ''
  const lose = centerCount[1] === '5'

  let scoreText = null
  await sharp(screenshot)
    .extract({
      top: 21,
      left: 130,
      width: 370,
      height: 30
    })
    .toFile('score.png')
  scoreText = await ocr('score.png')

  const image = await sharp(screenshot)
    .extract({
      // top: 100,
      // height: 300,
      top: 0,
      height: 400,
      left: 0,
      width: 640
    })
    .toBuffer()

  return {
    image,
    lose,
    score: parseFloat(scoreText)
  }
}

// puppeteer
;(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    // args: [
    //   `--disable-extensions-except=${PEPPER}`,
    //   `--load-extension=${PEPPER}`
    // ]
  })
  const page = await browser.newPage()
  await page.goto('http://localhost:8000/game/', {waitUntil: 'domcontentloaded'})
  await sleep(2000)
  page.mouse.click(10, 10)
  console.log('Game Loaded.')

  Bus.operate = async operation => {
    console.log(`Operation: `, operation)

    const promises = []
    for (let key in operation) {
      if (key === 'restart') {
        promises.push((async () => {
          console.log('restart')
          await page.keyboard.down(`Space`)
        })())
      } else {
        const duration = operation[key]
        key = key.toUpperCase()
        promises.push((async () => {
          console.log('keydown', key)
          await page.keyboard.down(`Key${key}`)
          await sleep(duration)
          console.log('keyup', key)
          await page.keyboard.up(`Key${key}`)
        })())
      }
    }

    Promise.all(promises)
    const screenshot = await page.screenshot({clip: {x: 0, y: 0, width: 640, height: 400}})
    // console.log(screenshot, screenshot.byteLength, screenshot.length, screenshot.toString())
    const res = await parseScreenshot(screenshot)
    return res
  }

  // console.log(await Bus.operate())
  // await browser.close()
})()
// return
// Koa
app.use(async ctx => {
  const operation = ctx.request.query
  console.log(operation)

  const res = await Bus.operate(operation)

  ctx.status = 200
  ctx.type = 'png'
  ctx.body = JSON.stringify(res)
})

app.listen(config.port)
