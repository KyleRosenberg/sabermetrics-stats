let arr_all_stats = [];
let dic_default_act = { 'const': 1 };
let dic_act_stats = $.extend(true, {}, dic_default_act);
let dic_sav_stats = {};

$(document).ready(function(event) {
    console.log('Sandbox ready!');
    stat_items = $('.stat_item')
    for (let i = 0; i < stat_items.length; i++) {
        si = stat_items[i];
        arr_all_stats.push(si.innerText);
    }
    $('.stat_bar .stat_item .ui.icon.button').click(addStat);
    $('.stat_bar .ui.fluid.selection.dropdown').dropdown({
        onChange: getGroupInfo
    });
    $('#btn_visualize').click(submitStat);
    $('#btn_savestat').click(saveStat);
    updateActiveStats();
});

function addStat() {
    let st = $(this)[0].name.substring(4);
    let exp = 1;
    let key = st + exp;
    while (key in dic_act_stats) {
        exp += 1;
        key = st + exp;
    }
    dic_act_stats[key] = [1, 1];
    updateActiveStats()
}

function removeStat() {
    let st = $(this)[0].name.substring(4);
    if (st in dic_act_stats) {
        delete dic_act_stats[st]
    }
    updateActiveStats()
}

function updateActiveStats() {
    let cont = $('.active_bar #stat_container');
    cont.empty();
    cont.append(`<div class="stat_item">
        <button class="ui icon button" name="btn_const">
            <i class="red minus circle icon"></i>
        </button>
        <label>Constant:</label>
        <div class="ui input">
            <input type="number" name="coef_const" value="${dic_act_stats['const']}">
        </div>
    </div>`)
    for (stat in dic_act_stats) {
        if (stat=='const'){
            continue;
        }
        info = dic_act_stats[stat];
        cont.append(`<div class="stat_item">
            <button class="ui icon button" name="btn_${stat}">
                <i class="red minus circle icon"></i>
            </button>
            <div class="ui input">
                <input type="number" name="coef_${stat}" value="${info[0]}">
            </div>
            <label> x ${stat.replace(/\d+$/, "")}^</label>
            <div class="ui input">
                <input type="number" name="exp_${stat}" value="${info[1]}">
            </div>
        </div>`)
    }
    $('.active_bar .stat_item .ui.icon.button').click(removeStat);
    $('.active_bar .stat_item .ui.input input').change(updateNumbers);
    renderEquation();
}

function updateNumbers() {
    let name = $(this)[0].name;
    if (name=='coef_const'){
        dic_act_stats['const'] = parseFloat($(this).val());
    } else {
        let index = 0;
        if (name.startsWith('exp_')) {
            index = 1;
            name = name.substring(4);
        } else {
            index = 0;
            name = name.substring(5);
        }
        let entry = dic_act_stats[name];
        entry[index] = parseFloat($(this).val());
        dic_act_stats[name] = entry;
    }
    renderEquation();
}

function updateAllStats(clearActive = true) {
    let cont = $('.stat_bar #stat_container');
    cont.empty();
    for (let i = 0; i < arr_all_stats.length; i++) {
        stat = arr_all_stats[i]
        cont.append(`<div class="stat_item">
            <button class="ui icon button" name="btn_${stat}">
                <i class="green plus circle icon"></i>
            </button>
            <label>${stat}</label>
        </div>`)
    }
    $('.stat_bar .stat_item .ui.icon.button').click(addStat);
    if (clearActive) {
        dic_act_stats = $.extend(true, {}, dic_default_act);
        updateActiveStats();
    }
}

function buildMarkupString(dict) {
    let ret = "";
    if (Object.keys(dict).length == 0) {
        ret = "1";
    } else {
        for (stat in dict) {
            let entry = dict[stat];
            ret += entry[0];
            ret += " \\times ";
            ret += stat.replace(/\d+$/, "");
            ret += "^{";
            ret += entry[1];
            ret += "} + ";
        }
    }
    return ret;
}

function renderEquation() {
    let numerator = {};
    let denominator = {};
    //First pass to separate
    for (stat in dic_act_stats) {
        if (stat=='const') continue;
        let entry = dic_act_stats[stat];
        if (entry[1] > 0) {
            numerator[stat] = entry.slice();
        } else {
            denominator[stat] = entry.slice();
            denominator[stat][1] *= -1; //Make positive now that we know its on the bottom
        }
    }
    let numer_string = buildMarkupString(numerator);
    if (numer_string.endsWith(' + ')) {
        numer_string = numer_string.slice(0, -3);
    }
    let denom_string = buildMarkupString(denominator);
    if (denom_string.endsWith(' + ')) {
        denom_string = denom_string.slice(0, -3);
    }
    $('.equation_box').empty();
    $('.equation_box').append(`$$\{\{${numer_string}\\over${denom_string}\} + ${dic_act_stats['const']}\}$$`);
    MathJax.Hub.Queue(["Typeset", MathJax.Hub]);
}

function getGroupInfo(name, text, choice) {
    $.ajax({
        type: 'POST',
        url: '/groupinfo',
        data: {
            'group': name
        },
        success: function(data) {
            arr_all_stats = data;
            updateAllStats();
        },
        error: console.log
    });
}

function submitStat() {
    $.ajax({
        type: 'POST',
        url: '/visualize',
        data: {
            'group': $('.stat_bar .ui.fluid.selection.dropdown input')[0].value,
            'equation': JSON.stringify(dic_act_stats),
            'name': $('#stat_name')[0].value,
            'customs': JSON.stringify(dic_sav_stats)
        },
        success: function(data) {
            $('.visualization').remove();
            $('.center_content').append(data);
        },
        error: console.log
    });
}

function saveStat(){
    let equation = dic_act_stats;
    let name = $('#stat_name')[0].value;
    dic_sav_stats[name] = equation;
    if (arr_all_stats.indexOf(name)==-1){
        arr_all_stats.push(name);
    }
    updateAllStats();
}
