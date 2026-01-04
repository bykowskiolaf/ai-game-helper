ProxiHUD = {}
ProxiHUD.name = "ProxiHUD_Bridge"

function ProxiHUD.OnPlayerUnloaded()
    ProxiHUD_Data = {
        timestamp = os.time(),
        name = GetUnitName("player"),
        level = GetUnitLevel("player"),
        class = GetUnitClass("player"),
        role = GetSelectedLFGRole(),
        equipment = {},
        inventory = {}
    }

    -- Scan Equipment
    for i = 0, 18 do 
        local link = GetItemLink(BAG_WORN, i)
        if link ~= "" then
            table.insert(ProxiHUD_Data.equipment, {
                slot = i, 
                name = GetItemLinkName(link), 
                link = link
            })
        end
    end

    -- Scan Backpack
    local bagCache = SHARED_INVENTORY:GenerateFullSlotData(nil, BAG_BACKPACK)
    for _, data in pairs(bagCache) do
        table.insert(ProxiHUD_Data.inventory, {
            name = data.name,
            count = data.stackCount,
            quality = data.quality,
            trait = GetItemTrait(BAG_BACKPACK, data.slotIndex)
        })
    end
end

EVENT_MANAGER:RegisterForEvent(ProxiHUD.name, EVENT_PLAYER_DEACTIVATED, ProxiHUD.OnPlayerUnloaded)