#!/usr/bin/env node
// Wrapper to run showdown on stdin input.
require("showdown")
process.stdin.setEncoding('utf8')
var input = ''
process.stdin.on('readable', function() {
  var chunk = process.stdin.read()
  if (chunk !== null ) {
    input += chunk
  }
})
process.stdin.on('end', function() {
  var Showdown = require('showdown')
  var converter = new Showdown.converter()
  process.stdout.write(converter.makeHtml(input))
})
