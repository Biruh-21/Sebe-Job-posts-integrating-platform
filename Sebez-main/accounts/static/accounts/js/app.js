$(document).ready(function () {
    // CSRF protection used by django for POST requests
    var csrf_token = $("input[name=csrfmiddlewaretoken]").val()

    // AJAX request to save/unsave posts
    $(".bookmark").off("click").on("click", function () {
        const $this = $(this); // clicked button
        const job_id = $this.val();

        $.ajax({
            method: "POST",
            url: "/ac/bookmark/",
            data: {
                job_id: job_id,
                csrfmiddlewaretoken: csrf_token,
            },
            statusCode: {
                200: function (response) {
                    clicked_btn = $("button[value='" + response["job_id"] + "']")
                    if (response["is_bookmarked"] == true) {
                        $this.html('<i class="fas fa-bookmark me-2"></i>Unsave');
                    } else {
                        $this.html('<i class="far fa-bookmark me-2"></i>Save');
                    }
                },
                401: function (response) {
                    window.location.reload();
                }
            }
        })
    })

    // AJAX request to move application to contacted list
    $(".contact").off("click").on("click", function () {
        const $this = $(this); // clicked button
        const ap_id = $this.val();

        $.ajax({
            method: "POST",
            url: "/contact/",
            data: {
                ap_id: ap_id,
                csrfmiddlewaretoken: csrf_token,
            },
            statusCode: {
                200: function (response) {
                    clicked_btn = $("button[value='" + response["ap_id"] + "']")
                    window.location.reload();
                },
                401: function (response) {
                    window.location.reload();
                }
            }
        })
    })


    // AJAX request to move application to contacted list
    $(".shortlist").off("click").on("click", function () {
        const $this = $(this); // clicked button
        const ap_id = $this.val();

        $.ajax({
            method: "POST",
            url: "/shortlist/",
            data: {
                ap_id: ap_id,
                csrfmiddlewaretoken: csrf_token,
            },
            statusCode: {
                200: function (response) {
                    clicked_btn = $("button[value='" + response["ap_id"] + "']")
                    window.location.reload();
                },
                401: function (response) {
                    window.location.reload();
                }
            }
        })
    })

    // AJAX request to move application to contacted list
    $(".archive").off("click").on("click", function () {
        const $this = $(this); // clicked button
        const ap_id = $this.val();

        $.ajax({
            method: "POST",
            url: "/archive/",
            data: {
                ap_id: ap_id,
                csrfmiddlewaretoken: csrf_token,
            },
            statusCode: {
                200: function (response) {
                    clicked_btn = $("button[value='" + response["ap_id"] + "']")
                    window.location.reload();
                },
                401: function (response) {
                    window.location.reload();
                }
            }
        })
    })

})