/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(__webpack_require__.s = "./src/smartech-crossasset.js");
/******/ })
/************************************************************************/
/******/ ({

/***/ "./src/smartech-crossasset.js":
/*!************************************!*\
  !*** ./src/smartech-crossasset.js ***!
  \************************************/
/*! no static exports found */
/***/ (function(module, exports) {

function _typeof(obj) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (obj) { return typeof obj; } : function (obj) { return obj && "function" == typeof Symbol && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; }, _typeof(obj); }
// allowed message types
var actions = ["setIdentity", "getIdentity", "setActivity", "getUnsyncedActivities"];

// trim white list urls to include only the origin
var originList = [];
for (var i = 0; i < whitelist.length; i++) {
  var parts = whitelist[i].split("/");
  originList.push(parts[0] + "//" + parts[2]);
}

// watch incoming messages
function messageHandler(event) {
  try {
    if (!originList.includes(event.origin) || !(event.data && _typeof(event.data) === "object" && "action" in event.data && actions.includes(event.data.action))) {
      return;
    }
    switch (event.data.action) {
      case "setIdentity":
        setIdentity(event.data.message);
        break;
      case "getIdentity":
        getIdentity(event.origin);
        break;
      case "setActivity":
        setActivity(event.data.message.eventName, event.data.message.eventPayload, event.origin);
        break;
      case "getUnsyncedActivities":
        getUnsyncedActivities(event.origin);
        break;
    }
  } catch (err) {}
}
window.addEventListener("message", messageHandler, false);

// sends a message to the parent container
function sendMessage(payload, origin, type) {
  var message = {
    origin: origin,
    payload: payload,
    type: type
  };
  parent.postMessage(message, "*");
}

// set new identity
function setIdentity(identity) {
  var idtyMap;
  try {
    idtyMap = JSON.parse(window.localStorage.getItem("__idty")) || {};
  } catch (error) {
    idtyMap = {};
  }

  // set identity of the domain along with the timestamp
  idtyMap[origin] = {
    idty: identity,
    ts: Date.now()
  };
  window.localStorage.setItem("__idty", JSON.stringify(idtyMap));
}

// pass new identity back to parent
function getIdentity(origin) {
  var idtyMap;
  try {
    idtyMap = JSON.parse(window.localStorage.getItem("__idty")) || {};
  } catch (error) {
    idtyMap = {};
  }

  // get the identity stored for the current domain making the request
  // const currentDomainIdty =
  //     idtyMap[origin] && "idty" in idtyMap[origin]
  //         ? idtyMap[origin].idty
  //         : undefined;
  // if (!currentDomainIdty) {
  //   return;
  // }

  var latestTimestamp = idtyMap[origin] && "idty" in idtyMap[origin] && "ts" in idtyMap[origin] ? idtyMap[origin].ts : 0;
  var latestIdty;

  // find the most recent identity
  for (var key in idtyMap) {
    if (Object.hasOwnProperty.call(idtyMap, key)) {
      if (idtyMap[key].ts >= latestTimestamp) {
        latestIdty = idtyMap[key].idty;
        latestTimestamp = idtyMap[key].ts;
      }
    }
  }
  if (!latestIdty) {
    return;
  }
  sendMessage(latestIdty, origin, "identity");
}
// set a new activity into along with sync state to idb
function setActivity(eventName, eventPayload, eventOrigin) {
  var dbReq = indexedDB.open("smt-activities", 1);
  dbReq.onupgradeneeded = function (event) {
    var db = event.target.result;
    if (!db.objectStoreNames.contains("events")) {
      db.createObjectStore("events", {
        autoIncrement: true
      });
    } else {
      dbReq.transaction.objectStore("events");
    }
  };
  dbReq.onsuccess = function (event) {
    // Start a database transaction and get the events object store
    var tx = event.target.result.transaction(["events"], "readwrite");
    var store = tx.objectStore("events");
    // Put the event into the object store
    var evt = {
      eventName: eventName,
      eventPayload: eventPayload,
      eventOrigin: eventOrigin,
      eventSync: getDefaultSyncState(eventOrigin),
      timestamp: Date.now()
    };
    store.add(evt);
    // Wait for the database transaction to complete
    tx.oncomplete = function () {
      console.log("stored note!");
    };
    tx.onerror = function (event) {
      console.error("error storing note " + event.target.errorCode);
    };
  };
}

// get all unsynced activities
function getUnsyncedActivities(origin) {
  var dbReq = indexedDB.open("smt-activities", 1);
  dbReq.onupgradeneeded = function (event) {
    var db = event.target.result;
    if (!db.objectStoreNames.contains("events")) {
      db.createObjectStore("events", {
        autoIncrement: true
      });
    }
  };
  dbReq.onsuccess = function (event) {
    var transaction = event.target.result.transaction(["events"], "readwrite");
    var objectStore = transaction.objectStore("events");
    var eventList = [];
    objectStore.openCursor().onsuccess = function (event) {
      var cursor = event.target.result;
      if (cursor) {
        if (cursor.value.eventSync[origin] === false) {
          var updateData = cursor.value;
          cursor.value.eventSync[origin] = true;
          eventList.push(cursor.value);
          var request = cursor.update(updateData);
          request.onsuccess = function () {};
        }
        cursor["continue"]();
      } else {
        if (eventList.length > 0) {
          sendMessage(eventList, origin, "activity");
        }
      }
    };
  };
}

// genarate default activity sync state
function getDefaultSyncState(origin) {
  var syncState = {};
  for (var _i = 0; _i < originList.length; _i++) {
    if (origin !== originList[_i]) {
      syncState[originList[_i]] = false;
    }
  }
  return syncState;
}

/***/ })

/******/ });
//# sourceMappingURL=smartech-crossassetv4.js.map