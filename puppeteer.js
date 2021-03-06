const puppeteer = require('puppeteer-extra')
const Koa = require('koa')
const fs = require('fs')
const getPixels = require('get-pixels')
const tesseract = require('node-tesseract')
const sharp = require('sharp')

const readline = require('readline')
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
})


const config = JSON.parse(fs.readFileSync('config.json'))

const app = new Koa()
const Bus = {
  buffer: ''
}

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

async function parseScreenshot (screenshot) {
  const ps = await pixels(screenshot)
  const center = ps.hi(164, 133).lo(148, 117).data // [148:164, 117:133]

  const centerCount = center.reduce((s, x) => s + x, 0) / center.length
  console.log(centerCount)
  const lose = (centerCount > 140)

  // let scoreText = null

  let t0 = new Date().getTime()

  // await sharp(screenshot)
  //   .extract({
  //     top: parseInt(21),
  //     left: parseInt(130),
  //     width: parseInt(370),
  //     height: parseInt(30)
  //   })
  //   .toFile('score.png')

  // console.log('   parseScreenshot.getOcrImage duration: ', -t0 + (t0 = new Date().getTime()))

  // scoreText = await ocr('score.png')

  // console.log('   parseScreenshot.ocr duration: ', -t0 + (t0 = new Date().getTime()))

  // scoreText = scoreText.replace(/o|O/g, 0).replace(/l|i|I/g, 1).replace(/L/g, '1.')

  const image = await sharp(screenshot)
    .extract({
      top: parseInt(20),
      height: parseInt(360),
      left: parseInt(120),
      width: parseInt(360)
    })
    .toBuffer()

  console.log('   parseScreenshot.sharpScreenshot duration: ', -t0 + (t0 = new Date().getTime()))

  // console.log('Score Text: ', scoreText)
  return {
    image,
    lose
    // score: parseFloat(scoreText)
  }
}

// puppeteer
;(async () => {
  const browser = await puppeteer.launch({
    headless: false
    // args: [
    //   `--disable-extensions-except=${PEPPER}`,
    //   `--load-extension=${PEPPER}`
    // ]
  })
  const page = await browser.newPage()
  await page.goto('http://localhost:8000/game', {waitUntil: 'domcontentloaded'})
  await sleep(2000)
  await page.mouse.click(300, 300)
  // await sleep(1000)
  // await page.mouse.click(10, 10)
  console.log('Game Loaded.')
  await page.evaluateHandle(() => window.paused = true)

  Bus.operate = async operation => {
    console.log(`Operation: `, operation)

    let t0 = new Date().getTime()

    await page.evaluateHandle(() => window.paused = false)

    const promises = []
    for (let key in operation) {
      if (key === 'restart') {
        promises.push((async () => {
          console.log('restart')
          await page.keyboard.press(`Space`)
        })())
      } else {
        const duration = operation[key]
        key = key.toUpperCase()
        promises.push((async () => {
          // console.log('keydown', key)
          await page.keyboard.down(`Key${key}`)
          await sleep(duration)
          // console.log('keyup', key)
          await page.keyboard.up(`Key${key}`)
        })())
      }
    }

    await Promise.all(promises)
    console.log(' operation duration: ', -t0 + (t0 = new Date().getTime()))
    const screenshot = await page.screenshot({clip: {x: 0, y: 0, width: 640, height: 400}})
    page.evaluateHandle(() => window.paused = true)
    
    console.log(' screenshot duration: ', -t0 + (t0 = new Date().getTime()))
    // console.log(screenshot, screenshot.byteLength, screenshot.length, screenshot.toString())
    const res = await parseScreenshot(screenshot)
    console.log(' parseScreenshot duration: ', -t0 + (t0 = (new Date().getTime())))
    Object.assign(res, {
      score: await page.evaluateHandle(() => window.score).then(h => h.jsonValue())
    })
    return res
  }
  rl.on('line', line => {
    try {
      console.log(eval(line))
    } catch (err) {
      console.log(err)
    }
  })
  // console.log(await Bus.operate())
  // await browser.close()
})()
// return
// Koa
app.use(async ctx => {
  const operation = ctx.request.query
  console.log('---'.repeat(10) + '\n\n')
  console.log(operation)

  let t0 = new Date().getTime()
  const res = await Bus.operate(operation)
  console.log('Koa duration: ', -t0 + (t0 = (new Date().getTime())))

  ctx.status = 200
  ctx.type = 'png'
  ctx.body = JSON.stringify(res)
})

app.listen(config.port)
