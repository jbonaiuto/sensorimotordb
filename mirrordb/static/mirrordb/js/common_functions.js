function getTRTag(idx)
{
    if(idx%2==0)
        return 'even_row';
    else
        return 'odd_row';
}

function clearSpan(doc, spanId)
{
    if(doc.getElementById(spanId)!=null)
        doc.getElementById(spanId).innerHTML='';
    return false;
}