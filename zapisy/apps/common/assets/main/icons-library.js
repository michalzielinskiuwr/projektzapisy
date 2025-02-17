/*  This is a FontAwesome icon library for System Zapisów.
    To use a new icon, find it in a cheatsheet
    https://fontawesome.com/cheatsheet and add it to our collection. It can be
    used in any template in the project, just like with the typical FontAwesome
    set-up, except we do not include all the icons.
*/
import { library, dom } from "@fortawesome/fontawesome-svg-core";

import { faCalendarAlt } from "@fortawesome/free-solid-svg-icons/faCalendarAlt";
library.add(faCalendarAlt);

import { faExternalLinkAlt } from "@fortawesome/free-solid-svg-icons/faExternalLinkAlt";
library.add(faExternalLinkAlt);

import { faPrint } from "@fortawesome/free-solid-svg-icons/faPrint";
library.add(faPrint);

import { faPlus } from "@fortawesome/free-solid-svg-icons/faPlus";
library.add(faPlus);

import { faMinus } from "@fortawesome/free-solid-svg-icons/faMinus";
library.add(faMinus);

import { faCarSide } from "@fortawesome/free-solid-svg-icons/faCarSide";
library.add(faCarSide);

import { faThumbtack } from "@fortawesome/free-solid-svg-icons/faThumbtack";
library.add(faThumbtack);

import { faBan } from "@fortawesome/free-solid-svg-icons/faBan";
library.add(faBan);

import { faPencilAlt } from "@fortawesome/free-solid-svg-icons/faPencilAlt";
library.add(faPencilAlt);

import { faCheck } from "@fortawesome/free-solid-svg-icons/faCheck";
library.add(faCheck);

import { faTimes } from "@fortawesome/free-solid-svg-icons/faTimes";
library.add(faTimes);

// This allows us to include an icon with <i class="fa fa-[ICON-NAME]"></i>.
dom.watch();
