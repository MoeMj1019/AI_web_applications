function clearSearch() {
    document.getElementById("searchInput").value = "";
    document.getElementById("clearButton").style.visibility = "hidden"; // Hide button when input is cleared
}

function showClearButton() {
    if (document.getElementById("searchInput").value.length > 0) {
        document.getElementById("clearButton").style.visibility = "visible";
    } else {
        document.getElementById("clearButton").style.visibility = "hidden";
    }
}


$(document).ready(function() {
    $('#loadMoreButton').click(function() {
        var query = $('#hiddenSearchInput').val();
        var currentPage = parseInt($('#currentPage').val()) + 1; 
        
        // console.log('Query:', query);
        // console.log('Current page:', currentPage);

        $.ajax({
            url: '/search',
            type: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest' 
            },
            data: {
                q: query,
                page: currentPage
            },
            success: function(response) {

                // console.log('AJAX Response:', response);

                $('.result-list').append(response.links_info.map(function(info) {
                    return '<li>' + 
                               '<a href="' + info.url + '"><h3>' + info.title + '</h3></a>' +
                               '<p class="url">' + info.url + '</p>' +
                               '<p class="highlight">' + info.highlight + ' ...</p>' +
                               '<p class="description">' + info.description + '</p>' +
                               '<p class="last-updated">Last updated: ' + info.time_stamp + '</p>' +
                           '</li>';
                }).join(''));

                $('#currentPage').val(currentPage); 
            },
            error: function(xhr, status, error) {
                console.error("Error loading more results:", error);
                // console.error("Status:", status);
                // console.error("Response:", xhr);
            }
        });
    });
});