map_file_id = 'AgACAgIAAxkBAAMCYm1aXw7QlMn536gpMT60LzGLFogAAiW4MRt1nHFLm_GfL_ENXKYBAAMCAAN5AAMkBA'
symbollist=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
           '1','2','3','4','5','6','7','8','9','0']


nearlocs={'spystart':['leftcorridor','rightcorridor','midcorridor'],
          'leftcorridor':['spystart','treasure','leftpass'],
          'rightcorridor':['spystart','treasure', 'rightpass'],
          'rightpass':['rightcorridor','stock'],
          'leftpass':['stock','leftcorridor'],
          'treasure':['leftcorridor','rightcorridor','stock','midcorridor'],
          'spystart':['leftcorridor','rightcorridor','midcorridor'],
          'midcorridor':['spystart','treasure'],
          'stock':['rightpass','leftpass','treasure']
}
nearlocs2={
'a1':['a2','b1'],
    'a2':['a1','a3','b2'],
    'a3':['a2','a4','b3'],
    'a4':['a3','b4'],
    'b1':['a1','b2','c1'],
    'b2':['b1','a2','b3','c2'],
    'b3':['b2','a3','b4','c3'],
    'b4':['b3','a4','c4'],
    'c1':['b1','c2','d1'],
    'c2':['c1','b2','c3','d2'],
    'c3':['c2','b3','c4','d3'],
    'c4':['c3','b4','d4'],
    'd1':['c1','d2','e1'],
    'd2':['d1','c2','d3','e2'],
    'd3':['d2','c3','d4','e3'],
    'd4':['d3','c4','e4'],
    'e1':['d1','e2'],
    'e2':['e1','d2','e3'],
    'e3':['e2','d3','e4'],
    'e4':['e3','d4']
}
