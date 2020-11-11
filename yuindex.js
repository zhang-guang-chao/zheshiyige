#! /usr/bin/env node

const fs = require('fs')
const { type } = require('os')
// const inquirer = require('inquirer')
// const program = require('commander')
// program
// .version('0.0.1')
// .option('-C, --chdir <path>', '这是不知道干嘛的')
// .option('-c, --config <path>', 'set config path. defaults to ./deploy.conf')
// .option('-T, --no-tests', 'ignore test hook')


// program
// .command('create <name>')
// .description('用来创建一个项目')
// .action(function(name, aaa) {
//   const promptList = [
//     {
//       type: 'input',
//       message: '设置一个用户名:',
//       name: 'name',
//       default: "test_user" // 默认值
//     },
//     {
//       type: 'confirm',
//       message: '是否需要路由:',
//       name: 'router',
//       default: false // 默认值
//     },
//     {
//       type: 'list',
//       message: '选择css预处理器',
//       choices: [
//         "Sass",
//         "Scss",
//         "Less"
//       ],
//       name: 'style',
//       default: 'Scss' // 默认值
//     },
//     {
//       type: 'checkbox',
//       message: '其他选择',
//       choices: [
//         "eslint",
//         "vuex",
//         "redux"
//       ],
//       name: 'outer',
//       default: [] // 默认值
//     }
//   ]
//   inquirer.prompt(promptList).then(answers => {
//     console.log(answers); // 返回的结果

//     fs.mkdir(name,(err,data)=>{
//       if (err) {
//         console.log(err);
//       } else{
//         console.log('创建一个' + name + '项目');
//       }
//     })
//   })
  
// });

// program
// .command('update <name>')
// .description('用来更新一个项目')
// .action(function(name, aaa) {
//   fs.mkdir(name,(err,data)=>{
//     if (err) {
//       console.log(err);
//     } else{
//       console.log('更新一个' + name + '项目');
//     }
//   })
// });



// program.parse(process.argv);


function readdir (path) {
  return fs.readdirSync(path)
}

/**
 * @param {*} tree 树状结构数据
 * @return {String} 树状结构字符串
 */
function transformation (tree, level = 1) {

  const keys = Object.keys(tree)
  let JSONString = ''

  keys.forEach((name) => {
    const value = tree[name]
    if (typeof value === 'object') {
      JSONString += '├──'.repeat(level) + name + '\n'
      JSONString += transformation(value, level + 1)
    } else {
      JSONString += '├──'.repeat(level) + name + '\n'
    }
  })
  return JSONString
}

function readTreeDir (path, dirChildren, exclude) {
  const dirJSON = {}
  dirChildren.forEach((name) => {
    const file = fs.statSync(path+ '/' +name)

    if (file.isDirectory()) {
      if (name !== exclude) {
        dirJSON[name] = readTreeDir( path+ '/' +name, readdir(path+ '/' +name), exclude )
      }
    } else {
      const file = name.split('.')
      dirJSON[file[0]] = file[1]
    }
  })

  return dirJSON
}

function run (argv) {

  console.log(argv)

  const arg = (argv[0] && argv[0].split('=') ) || []
  const value = arg[1]

  console.log(value)

  const dirChildren = readdir(process.cwd())

  const dirJSON = readTreeDir(process.cwd(), dirChildren, value)

  // console.log(JSON.stringify(dirJSON))

  const JSONString = transformation(dirJSON)

  console.log(JSONString)


  // if (argv[0] === '-v' || argv[0] === '--version') {

  //     console.log('version is 0.0.2');

  // } else if (argv[0] === '-h' || argv[0] === '--help') {

  //     console.log('  usage:\n');
  //     console.log('  -v --version [show version]');

  // }


  

}

run(process.argv.slice(2));

/**
├── .vscode                                                                                                                                                      
├── ├── launch.json                                                                                                                                              
├── README.md                                                                                                                                                    
├── d                                                                                                                                                            
├── ├── dd                                                                                                                                                       
├── ├── hehe                                                                                                                                                     
├── ├── ├── hehe                                                                                                                                                 
├── index.js                                                                                                                                                     
├── j.js                                                                                                                                                         
├── package.json    
 */ 