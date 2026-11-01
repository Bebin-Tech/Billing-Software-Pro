import ts from '../frontend/node_modules/typescript/lib/typescript.js';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../frontend');
const config=ts.readConfigFile(path.join(root,'tsconfig.json'),ts.sys.readFile);
const parsed=ts.parseJsonConfigFileContent(config.config,ts.sys,root);
const host={getScriptFileNames:()=>parsed.fileNames,getScriptVersion:()=> '0',getScriptSnapshot:file=>fs.existsSync(file)?ts.ScriptSnapshot.fromString(fs.readFileSync(file,'utf8')):undefined,getCurrentDirectory:()=>root,getCompilationSettings:()=>parsed.options,getDefaultLibFileName:o=>ts.getDefaultLibFilePath(o),fileExists:ts.sys.fileExists,readFile:ts.sys.readFile,readDirectory:ts.sys.readDirectory};
const service=ts.createLanguageService(host);
for(const fileName of parsed.fileNames){
  if(fileName.endsWith('.d.ts'))continue;
  const edits=service.organizeImports({type:'file',fileName},{},{});
  for(const edit of edits){let source=fs.readFileSync(edit.fileName,'utf8');for(const change of [...edit.textChanges].sort((a,b)=>b.span.start-a.span.start))source=source.slice(0,change.span.start)+change.newText+source.slice(change.span.start+change.span.length);fs.writeFileSync(edit.fileName,source);}
}
console.log('Organized TypeScript imports.');
