function clearSearch() {
    var inputs = document.getElementsByClassName("bar-input");
    for (var i = 0; i < inputs.length; i++) {
        inputs[i].value = "";
    }
    document.getElementById("clearButton").style.visibility = "hidden"; 
}

function showClearButton() {
    var inputs = document.getElementsByClassName("bar-input");
    var anyInputHasValue = Array.from(inputs).some(input => input.value.length > 0);

    if (anyInputHasValue) {
        document.getElementById("clearButton").style.visibility = "visible";
    } else {
        document.getElementById("clearButton").style.visibility = "hidden";
    }
}

function validateSearch() {
    var searchInput = document.getElementById('searchInput').value.trim();
    if (searchInput === ''){
        alert('Please enter a valid search query.');
        return false; 
    }
    return true; 
}

function validateCrawlQueue() {
    var crawlInput = document.getElementById('crawlInput').value.trim();
    if (crawlInput === ''){
        alert('Please enter a valid crawl query.');
        return false; 
    }
    return true; 
}

$(document).ready(function() {
    $('#loadMoreButton').click(function() {
        var query = $('#hiddenSearchInput').val();
        var currentPage = parseInt($('#currentPage').val()) + 1; 
        
        // console.log('Query:', query);
        // console.log('Current page:', currentPage);

        $.ajax({
            url: searchUrl,
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


function openModal() {
    document.getElementById('indexModal').style.display = 'block';
}

// Function to close the modal
function closeModal() {
    document.getElementById('indexModal').style.display = 'none';
}

function setIndex() {
    var index = document.getElementById('indexSelect').value;
    var xhr = new XMLHttpRequest();
    xhr.open('POST', setIndexUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        if (xhr.status === 200) {
            // Update the displayed index
            var response = JSON.parse(xhr.responseText);
            updateDisplayedIndex(response.index);
        } else {
            console.error('Error setting index:', xhr.responseText);
        }
        // console.log('Index set to:', index);
    };
    xhr.send('index=' + encodeURIComponent(index));
}

function updateDisplayedIndex(index) {
    var indexValueElem = document.getElementById('index-value');
    if (indexValueElem) {
        indexValueElem.textContent = '"' + index + '"';
    } else {
        // Create the index value element if it doesn't exist
        var indexNameDiv = document.getElementById('index-name');
        indexValueElem = document.createElement('p');
        indexValueElem.id = 'index-value';
        indexValueElem.textContent = '"' + index + '"';
        indexNameDiv.appendChild(indexValueElem);
    }
}