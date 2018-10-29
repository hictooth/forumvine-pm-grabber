<?php

    $MESSAGE_FILE = "messages.json";

    // setup phpbb stuff
    define('IN_PHPBB', true);
    $phpbb_root_path = (defined('PHPBB_ROOT_PATH')) ? PHPBB_ROOT_PATH : '/var/www/forums.nightfury.net/html/';
    $phpEx = substr(strrchr(__FILE__, '.'), 1);
    include($phpbb_root_path . 'common.' . $phpEx);
    include($phpbb_root_path . 'includes/functions_user.' . $phpEx);


    function addMessage($message) {
        global $db;

        // encode the message text
        $bbcode = $message['text'];
        $uid = $bitfield = $options = '';
        generate_text_for_storage($bbcode, $uid, $bitfield, $options, true, true, true);

        // escape all the values
        $msg_id = $db->sql_escape($message['id']);
        $root_level = $db->sql_escape($message['top_id']);
        $author_id = $db->sql_escape($message['from_id']);
        $message_time = $db->sql_escape($message['timestamp']);
        $message_subject = $db->sql_escape($message['subject']);
        $message_text = $db->sql_escape($bbcode);
        $bbcode_bitfield = $db->sql_escape($bitfield);
        $bbcode_uid = $db->sql_escape($uid);
        $to_address = $db->sql_escape('u_' . $message['to_id']);

        // check this pm hasn't already been inserted
        $sql = "SELECT * FROM phpbb_privmsgs WHERE msg_id = '" . $msg_id . "'";
        $result = $db->sql_query($sql);

        if ($result->num_rows != 0) {
            // already inserted, skip this!
            return;
        }

        // build the statement
        $sql = "INSERT INTO phpbb_privmsgs VALUES('" . $msg_id . "', '"
                                                    . $root_level . "', '"
                                                    . $author_id . "', 0, '127.0.0.1', '"
                                                    . $message_time . "', 1, 1, 1, 1, '"
                                                    . $message_subject . "', '"
                                                    . $message_text . "', '', 0, 0, '"
                                                    . $bbcode_bitfield . "', '"
                                                    . $bbcode_uid . "', 0, 0, '"
                                                    . $to_address . "', '', 0)";

        // run the query
        echo $sql . "\n";
        $result = $db->sql_query($sql);
        /*if (!$result) {
            echo "error doing query!";
            die();
        }*/


        // escape some more stuff
        $user_id = $db->sql_escape($message['to_id']);
        $pm_replied = ($message['has_reply'] ? '1' : '0');

        // build the next statement (inserting into inbox)
        $sql = "INSERT INTO phpbb_privmsgs_to VALUES('" . $msg_id . "', '"
                                                    . $user_id . "', '"
                                                    . $author_id . "', 0, 0, 0, '"
                                                    . $pm_replied . "', 0, 0, 0)";

        // run the query
        echo $sql . "\n";
        $result = $db->sql_query($sql);
        /*if (!$result) {
            echo "error doing query!";
            die();
        }*/


        // escape some more stuff
        $user_id = $db->sql_escape($message['from_id']);

        // build the next statement (inserting into inbox)
        $sql = "INSERT INTO phpbb_privmsgs_to VALUES('" . $msg_id . "', '"
                                                    . $user_id . "', '"
                                                    . $author_id . "', 0, 0, 0, '"
                                                    . $pm_replied . "', 0, 0, -1)";

        // run the query
        echo $sql . "\n";
        $result = $db->sql_query($sql);
        /*if (!$result) {
            echo "error doing query!";
            die();
        }*/
    }


    // read the mesages from the file
    $contents = file_get_contents($MESSAGE_FILE);
    $messages = json_decode($contents, true);

    foreach ($messages as $message) {
        addMessage($message);
    }

?>
