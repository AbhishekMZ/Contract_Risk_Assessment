// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

contract Reentrancy {
    mapping(address => uint) private userBalances;

    function deposit() public payable {
        userBalances[msg.sender] += msg.value;
    }

    function withdrawBalance() public {
        uint amountToWithdraw = userBalances[msg.sender];
        // This is vulnerable to reentrancy
        if (msg.sender.call.value(amountToWithdraw)()) {
            userBalances[msg.sender] = 0;
        }
    }
}
