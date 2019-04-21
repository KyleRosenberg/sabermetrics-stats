let arr_all_stats = []
let arr_act_stats = []

$(document).ready(function(event) {
    console.log('Sandbox ready!');
    stat_items = $('.stat_item')
    for (let i = 0; i<stat_items.length; i++){
        si = stat_items[i];
        arr_all_stats.push(si.innerText);
    }
    $('.stat_bar .stat_item .ui.icon.button').click(addStat);
    $('.stat_bar .ui.fluid.selection.dropdown').dropdown({
        onChange: getGroupInfo
    });
});

function addStat(){
    let st = $(this)[0].name.substring(4);
    arr_act_stats.push(st);
    updateActiveStats()
}

function removeStat(){
    let st = $(this)[0].name.substring(4);
    let ind = arr_act_stats.indexOf(st);
    if (ind != -1){
        arr_act_stats.splice(ind, 1)
    }
    updateActiveStats()
}

function updateActiveStats(){
    let cont = $('.active_bar #stat_container');
    cont.empty();
    for (let i = 0; i<arr_act_stats.length; i++){
        stat = arr_act_stats[i]
        cont.append(`<div class="stat_item">
            <button class="ui icon button" name="btn_${stat}">
                <i class="red minus circle icon"></i>
            </button>
            <label>${stat}</label>
        </div>`)
    }
    $('.active_bar .stat_item .ui.icon.button').click(removeStat);
}

function updateAllStats(clearActive=true){
    let cont = $('.stat_bar #stat_container');
    cont.empty();
    for (let i = 0; i<arr_all_stats.length; i++){
        stat = arr_all_stats[i]
        cont.append(`<div class="stat_item">
            <button class="ui icon button" name="btn_${stat}">
                <i class="green plus circle icon"></i>
            </button>
            <label>${stat}</label>
        </div>`)
    }
    $('.stat_bar .stat_item .ui.icon.button').click(addStat);
    if (clearActive){
        arr_act_stats = [];
        updateActiveStats();
    }
}

function getGroupInfo(name, text, choice){
    $.ajax({
        type: 'POST',
        url: '/groupinfo',
        data: {
            'group': name
        },
        success: function(data){
            arr_all_stats = data;
            updateAllStats();
        },
        error: console.log
    });
}
