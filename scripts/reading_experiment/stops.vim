" Record where you stopped reading, without leaving the file.
"
" Open the reading copy with:
"     nvim -S stops.vim reading_copy.tex
"
" Then, while reading:
"     ,s   record this line, with a short note typed at the prompt
"     ,S   record this line with no note (faster)
"     ,q   mark this line as where you quit reading
"     ,l   list what you have recorded so far
"
" Everything is appended to stops.md beside the file you are reading, so
" nothing is lost if nvim dies, and you can edit that file by hand afterwards.

let s:stops = expand('%:p:h') . '/stops.md'

function! s:Append(text) abort
  if !filereadable(s:stops)
    call writefile(['# line  note', '# quit: <line>'], s:stops)
  endif
  call writefile([a:text], s:stops, 'a')
endfunction

function! s:Stop(ask) abort
  let l:note = ''
  if a:ask
    let l:note = input('why did you stop? ')
    redraw
  endif
  call s:Append(printf('%d  %s', line('.'), l:note))
  echo printf('recorded line %d  (%d so far)', line('.'), s:Count())
endfunction

function! s:Count() abort
  if !filereadable(s:stops)
    return 0
  endif
  return len(filter(readfile(s:stops), 'v:val !~# "^#" && v:val =~# "\\S"'))
endfunction

function! s:Quit() abort
  call s:Append(printf('# quit: %d', line('.')))
  echo printf('marked line %d as where you quit', line('.'))
endfunction

function! s:List() abort
  if !filereadable(s:stops)
    echo 'nothing recorded yet'
    return
  endif
  echo join(readfile(s:stops), "\n")
endfunction

nnoremap <silent> ,s :call <SID>Stop(1)<CR>
nnoremap <silent> ,S :call <SID>Stop(0)<CR>
nnoremap <silent> ,q :call <SID>Quit()<CR>
nnoremap <silent> ,l :call <SID>List()<CR>

setlocal number
setlocal nomodifiable
echo 'reading: ,s stop with note   ,S stop   ,q quit here   ,l list'
