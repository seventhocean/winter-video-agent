import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const catalog=JSON.parse(fs.readFileSync(fileURLToPath(new URL('../library/motion/catalog.json',import.meta.url)),'utf8'));
const query=process.argv.slice(2).join(' ').toLowerCase();
const results=catalog.items.filter(item=>!query||[item.id,item.purpose,...item.keywords].join(' ').toLowerCase().includes(query));
console.log(JSON.stringify({workflow:catalog.workflow,implementation:catalog.implementation,results},null,2));
